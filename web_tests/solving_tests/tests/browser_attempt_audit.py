"""Explicit browser regression suite; run with web_tests.test_settings.

Uses an isolated test database, including the background-expiry scenario.
"""
import json
import os
from datetime import timedelta
from urllib.parse import urlsplit
from unittest.mock import patch

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from create_tests.answer_storage import pack_answers
from create_tests.models import AboutExpressions, AboutTest, PublishedGroup, Subjects, TypeAnswer
from solving_tests.models import StudentResult, TestAttempt
from users.models import CustomUser, StudentData, StudentGroup, StudentInstitute, TeacherData


@override_settings(YANDEX_DISK_TOKEN='')
class AttemptLifecycleAudit(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Playwright's synchronous API owns an event loop on this test thread.
        # ORM operations here are sequential and target only the disposable test DB.
        guard = patch.dict(os.environ, {'DJANGO_ALLOW_ASYNC_UNSAFE': 'true'})
        guard.start()
        cls.addClassCleanup(guard.stop)
        from playwright.sync_api import sync_playwright
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(channel='chrome', headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        super().tearDownClass()

    def setUp(self):
        upload = patch('solving_tests.views.upload_test_attempt_log')
        self.upload = upload.start()
        self.addCleanup(upload.stop)
        institute = StudentInstitute.objects.create(name='Lifecycle audit')
        group = StudentGroup.objects.create(name='AUDIT-01', name_inst=institute)
        teacher_user = CustomUser.objects.create_user('audit.teacher@example.com', 'Audit2026!', role='teacher')
        teacher = TeacherData.objects.create(data_map=teacher_user, institute=institute,
                                             first_name='Audit', last_name='Teacher', middle_name='')
        self.student = CustomUser.objects.create_user('audit.student@example.com', 'Audit2026!', role='student')
        StudentData.objects.create(data_map=self.student, institute=institute, group=group,
                                   first_name='Audit', last_name='Student')
        subject = Subjects.objects.create(name='Lifecycle audit')
        self.test = AboutTest.objects.create(name_tests='Lifecycle audit', subj=subject, creator=teacher,
                                             is_published=1, num_of_attempts=20,
                                             time_to_solution=timedelta(seconds=60))
        PublishedGroup.objects.create(test_name=self.test, group_name=group, teacher_name=teacher)
        for number, (code, answer, choice) in enumerate([
            (1, '42', False),
            (4, r'\begin{pmatrix}1&2\\3&4\end{pmatrix}', False),
            (5, 'FREE_ANSWER', False),
            (1, pack_answers(['2', '3']), True),
        ], 1):
            kind, _ = TypeAnswer.objects.get_or_create(type_code=code, defaults={'name': str(code)})
            expression = AboutExpressions.objects.create(user_expression=str(number), user_ans=answer,
                user_type=kind, exist_select=choice, true_ans='1;0' if choice else '1',
                block_expression_num=number, number=number)
            self.test.expressions.add(expression)
        self.context = self.browser.new_context()
        self.addCleanup(self.context.close)
        # Block external resources; the audit only talks to its own local test server.
        host = urlsplit(self.live_server_url).netloc
        self.context.route('**/*', lambda route: route.continue_()
                           if urlsplit(route.request.url).netloc == host else route.abort())
        self.page = self.context.new_page()
        self.page.set_default_timeout(12000)
        self.solve_url = self.live_server_url + reverse('solving_tests:some_test_for_student', args=[self.test.name_slug_tests])
        self.login()

    def login(self):
        self.page.goto(self.live_server_url + '/', wait_until='domcontentloaded')
        self.page.locator('[name="email"]').fill(self.student.email)
        self.page.locator('[name="password"]').fill('Audit2026!')
        self.page.locator('form button[type="submit"]').first.click()
        self.page.wait_for_url('**/Home/')

    def open_test(self):
        self.page.goto(self.solve_url, wait_until='domcontentloaded')
        self.page.wait_for_function("customElements.get('math-field') && [...document.querySelectorAll('math-field')].every(el => typeof el.getValue === 'function')")

    def fill_answers(self):
        values = ['42', r'\begin{pmatrix}1&2\\3&4\end{pmatrix}', r'\text{Free explanation}']
        self.page.locator('.question-card math-field').evaluate_all("""(fields, values) => fields.forEach((el, i) => {
            el.value = values[i]; el.dispatchEvent(new Event('input', {bubbles: true}));
        })""", values)
        self.page.locator('.question-card input[type="checkbox"]').first.check()
        self.page.wait_for_function("document.getElementById('saveStatus').textContent === '\u0412\u0441\u0435 \u043e\u0442\u0432\u0435\u0442\u044b \u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u044b'")
        return self.answers()

    def answers(self):
        return self.page.locator('.question-card math-field').evaluate_all('(fields) => fields.map(el => el.value)')

    def seconds(self):
        return self.page.locator('#timer').evaluate("el => el.textContent.trim().split(':').map(Number).reduce((n, part) => n * 60 + part, 0)")

    def observe(self, **data):
        print('AUDIT ' + self._testMethodName + ': ' + json.dumps(data, ensure_ascii=True), flush=True)

    def test_refresh_preserves_answers_and_deadline(self):
        self.open_test()
        expected = self.fill_answers()
        deadline = TestAttempt.objects.get().deadline
        self.page.wait_for_timeout(2200)
        running = self.seconds()
        self.page.reload(wait_until='domcontentloaded')
        self.page.wait_for_function("document.querySelector('math-field').value === '42'")
        self.assertEqual(self.answers(), expected)
        self.assertTrue(self.page.locator('.question-card input[type="checkbox"]').first.is_checked())
        self.assertLessEqual(self.seconds(), running)
        self.assertEqual(TestAttempt.objects.get().deadline, deadline)
        self.assertEqual(StudentResult.objects.count(), 0)
        self.observe(restored=True, same_deadline=True)

    def test_leave_and_reenter_preserves_answers(self):
        self.open_test()
        expected = self.fill_answers()
        self.page.goto(self.live_server_url + reverse('solving_tests:list_test'), wait_until='domcontentloaded')
        self.open_test()
        self.page.wait_for_function("document.querySelector('math-field').value === '42'")
        self.assertEqual(self.answers(), expected)
        self.assertEqual(TestAttempt.objects.count(), 1)

    def test_logout_and_login_preserves_answers(self):
        self.open_test()
        expected = self.fill_answers()
        deadline = TestAttempt.objects.get().deadline
        self.page.evaluate("""async () => {
            const csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;
            await fetch('/logout/', {method: 'POST', headers: {'X-CSRFToken': csrf}});
        }""")
        self.login()
        self.open_test()
        self.page.wait_for_function("document.querySelector('math-field').value === '42'")
        self.assertEqual(self.answers(), expected)
        self.assertEqual(TestAttempt.objects.get().deadline, deadline)

    def test_tabs_share_attempt_and_merge_different_fields(self):
        self.open_test()
        expected = self.fill_answers()
        first = self.page
        self.page.wait_for_timeout(2200)
        running = self.seconds()
        self.page = self.context.new_page()
        self.open_test()
        self.page.wait_for_function("document.querySelector('math-field').value === '42'")
        self.assertEqual(self.answers(), expected)
        self.assertLessEqual(self.seconds(), running)
        # Both tabs initially have the same revision. Each edits a different answer.
        first.locator('math-field').first.evaluate("el => {el.value='43'; el.dispatchEvent(new Event('input',{bubbles:true}));}")
        self.page.locator('math-field').nth(2).evaluate("el => {el.value='new'; el.dispatchEvent(new Event('input',{bubbles:true}));}")
        self.page.wait_for_timeout(1200)
        attempt = TestAttempt.objects.get()
        self.assertEqual(attempt.answers[0], '43')
        self.assertEqual(attempt.answers[2], 'new')
        first.close()
        self.page.close()
        self.page = self.context.new_page()
        self.open_test()
        self.page.wait_for_function("document.querySelector('math-field').value === '43'")
        self.assertEqual(TestAttempt.objects.count(), 1)

    def test_timeout_submits_and_redirects_without_accepting_late_edits(self):
        self.test.time_to_solution = timedelta(seconds=5)
        self.test.save(update_fields=['time_to_solution'])
        self.open_test()
        expected = self.fill_answers()
        self.page.wait_for_url('**/result/', timeout=12000)
        attempt = TestAttempt.objects.get()
        result = StudentResult.objects.get()
        self.assertEqual(json.loads(result.res_answer)[:3], expected)
        self.assertEqual(result.completed_at, attempt.deadline)
        self.assertEqual(result.started_at, attempt.started_at)
        self.assertEqual(result.time_spent, timedelta(seconds=5))
        self.assertTrue(result.is_completed)
        response = self.client
        response.force_login(self.student)
        response.post(reverse('solving_tests:attempt_api', args=[self.test.name_slug_tests, attempt.pk]),
            json.dumps({'action': 'finish', 'revision': attempt.revision, 'changes': {'0': '999'}}),
            content_type='application/json')
        self.assertEqual(StudentResult.objects.count(), 1)
        attempt.refresh_from_db()
        self.assertEqual(attempt.answers[0], '42')
        self.observe(auto_submit=True, redirect=True, duplicate_safe=True, deadline_enforced=True)

    def test_manual_submit_saves_answers_and_shows_results(self):
        self.open_test()
        expected = self.fill_answers()
        self.page.locator('#answerForm button[type="submit"]').click()
        self.page.wait_for_url('**/result/')
        result = StudentResult.objects.get()
        self.assertEqual(json.loads(result.res_answer)[:3], expected)
        self.assertEqual(result.result_points, 3)
        self.assertTrue(result.is_completed)
        self.assertIsNotNone(result.completed_at)
        self.assertEqual(result.free_answer_grades.count(), 1)
        self.page.goto(self.solve_url, wait_until='domcontentloaded')
        self.assertTrue(self.page.url.endswith('/result/'))
        self.assertEqual(TestAttempt.objects.count(), 1)

    def test_closed_browser_is_finished_by_worker(self):
        import threading
        from solving_tests.expiry_worker import run
        self.test.time_to_solution = timedelta(seconds=5)
        self.test.save(update_fields=['time_to_solution'])
        self.open_test()
        expected = self.fill_answers()
        self.page.close()
        stop = threading.Event()
        worker = threading.Thread(target=run, args=(stop, 0.1), daemon=True)
        worker.start()
        try:
            import time
            end = time.monotonic() + 8
            while not StudentResult.objects.exists() and time.monotonic() < end:
                time.sleep(0.1)
            result = StudentResult.objects.get()
            self.assertEqual(json.loads(result.res_answer)[:3], expected)
            self.assertTrue(result.is_completed)
        finally:
            stop.set()
            worker.join(timeout=3)
        self.page = self.context.new_page()
        self.page.goto(self.solve_url, wait_until='domcontentloaded')
        self.assertTrue(self.page.url.endswith('/result/'))
        self.observe(closed_browser_finished=True, return_shows_result=True)

    def test_offline_draft_recovers_after_reload(self):
        self.open_test()
        self.fill_answers()
        self.context.set_offline(True)
        self.page.locator('math-field').first.evaluate("el => {el.value='43'; el.dispatchEvent(new Event('input',{bubbles:true}));}")
        self.page.wait_for_timeout(600)
        self.assertEqual(TestAttempt.objects.get().answers[0], '42')
        self.context.set_offline(False)
        self.page.reload(wait_until='domcontentloaded')
        self.page.wait_for_function("document.querySelector('math-field').value === '43'")
        self.page.wait_for_timeout(600)
        self.assertEqual(TestAttempt.objects.get().answers[0], '43')

    def test_immediate_reload_preserves_pending_input(self):
        self.open_test()
        self.fill_answers()
        self.page.locator('math-field').first.evaluate("el => {el.value='43'; el.dispatchEvent(new Event('input',{bubbles:true}));}")
        self.page.reload(wait_until='domcontentloaded')
        self.page.wait_for_function("document.querySelector('math-field').value === '43'")
        self.page.wait_for_timeout(700)
        self.assertEqual(TestAttempt.objects.get().answers[0], '43')

    def test_new_attempt_is_explicit_and_blank(self):
        self.open_test()
        self.fill_answers()
        self.page.locator('#answerForm button[type="submit"]').click()
        self.page.wait_for_url('**/result/')
        self.page.goto(self.live_server_url + reverse('solving_tests:list_test'), wait_until='domcontentloaded')
        self.page.locator('.test-footer form button[type="submit"]').click()
        self.page.wait_for_url(self.solve_url)
        self.page.wait_for_function("document.querySelectorAll('.question-card math-field').length === 3")
        self.assertEqual(self.answers(), ['', '', ''])
        self.assertEqual(TestAttempt.objects.count(), 2)
        self.assertEqual(StudentResult.objects.count(), 1)

    def test_real_runserver_finishes_attempt_without_browser(self):
        """Verify command discovery and the real runserver worker, not just its loop."""
        import socket
        import subprocess
        import sys
        import time
        from pathlib import Path
        from django.db import connection

        self.open_test()
        self.fill_answers()
        self.page.close()
        TestAttempt.objects.update(deadline=timezone.now() + timedelta(seconds=3))
        database = connection.settings_dict['NAME']
        self.assertTrue(database.startswith('test_'), 'Only disposable test MySQL is allowed')
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        env = os.environ.copy()
        env.pop('DJANGO_ALLOW_ASYNC_UNSAFE', None)
        env['DB_NAME'] = database
        env['PYTHONPATH'] = str(Path.cwd()) + os.pathsep + env.get('PYTHONPATH', '')
        process = subprocess.Popen([sys.executable, 'manage.py', 'runserver',
            f'127.0.0.1:{port}', '--noreload', '--settings=web_tests.test_settings'],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        try:
            end = time.monotonic() + 30
            completed = False
            while time.monotonic() < end and process.poll() is None:
                completed = StudentResult.objects.count() == 1
                if completed:
                    break
                time.sleep(0.2)
        finally:
            if os.name == 'nt':
                # Stop the test server AND its spawned grading processes, which
                # otherwise keep the inherited stderr pipe open on Windows.
                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                process.terminate()
            _, errors = process.communicate(timeout=10)
        self.assertTrue(completed, 'runserver must start its own worker: ' + errors.decode(errors='replace'))
        self.assertEqual(StudentResult.objects.count(), 1)
        self.observe(real_runserver_worker=True)
