import json
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from create_tests.models import AboutExpressions, AboutTest, PublishedGroup, Subjects, TypeAnswer
from users.models import CustomUser, StudentData, StudentGroup, StudentInstitute, TeacherData
from solving_tests.attempts import (RevisionConflict, expire_attempts, finish_attempt,
                                   start_attempt, update_attempt)
from solving_tests.models import StudentResult, TestAttempt


class AttemptTests(TestCase):
    def setUp(self):
        institute = StudentInstitute.objects.create(name='Attempt tests')
        group = StudentGroup.objects.create(name='ATT-01', name_inst=institute)
        teacher_user = CustomUser.objects.create_user('attempt.teacher@example.com', 'pass', role='teacher')
        teacher = TeacherData.objects.create(data_map=teacher_user, institute=institute,
                                             first_name='Test', last_name='Teacher', middle_name='')
        self.student = CustomUser.objects.create_user('attempt.student@example.com', 'pass', role='student')
        StudentData.objects.create(data_map=self.student, institute=institute, group=group,
                                   first_name='Test', last_name='Student')
        subject = Subjects.objects.create(name='Attempts')
        self.test = AboutTest.objects.create(name_tests='Attempts', subj=subject, creator=teacher,
                                             is_published=1, num_of_attempts=2,
                                             time_to_solution=timedelta(minutes=10))
        PublishedGroup.objects.create(test_name=self.test, group_name=group, teacher_name=teacher)
        kind, _ = TypeAnswer.objects.get_or_create(type_code=1, defaults={'name': 'Number'})
        self.question = AboutExpressions.objects.create(user_expression='2+2', user_ans='4',
            user_type=kind, number=1, block_expression_num=1, points_for_solve=2)
        self.test.expressions.add(self.question)
        self.client.force_login(self.student)

    def test_reopening_keeps_one_attempt_and_deadline(self):
        attempt = start_attempt(self.student, self.test)
        again = start_attempt(self.student, self.test)
        self.assertEqual(attempt.pk, again.pk)
        self.assertEqual(attempt.deadline, again.deadline)
        self.assertFalse(StudentResult.objects.exists())

    def test_draft_roundtrip_and_snapshot_survives_teacher_edits(self):
        attempt = start_attempt(self.student, self.test)
        update_attempt(attempt.pk, 0, {'0': '4'})
        self.question.user_ans = '999'
        self.question.user_expression = 'Changed'
        self.question.save()
        self.test.time_to_solution = timedelta(hours=9)
        self.test.save()
        again = start_attempt(self.student, self.test)
        self.assertEqual(again.answers, ['4'])
        self.assertEqual(again.deadline, attempt.deadline)
        self.assertEqual(finish_attempt(attempt.pk).result.result_points, 2)

    def test_stale_revision_is_rejected_without_losing_saved_answers(self):
        attempt = start_attempt(self.student, self.test)
        update_attempt(attempt.pk, 0, {'0': '4'})
        with self.assertRaises(RevisionConflict):
            update_attempt(attempt.pk, 0, {'0': '999'})
        attempt.refresh_from_db()
        self.assertEqual(attempt.answers, ['4'])
        self.assertEqual(attempt.revision, 1)

    def test_late_save_grades_only_previously_saved_answers(self):
        attempt = start_attempt(self.student, self.test)
        update_attempt(attempt.pk, 0, {'0': '4'})
        with patch('solving_tests.attempts.timezone.now', return_value=attempt.deadline + timedelta(seconds=1)):
            done = update_attempt(attempt.pk, 1, {'0': '999'}, finish=True)
        self.assertEqual(done.answers, ['4'])
        self.assertIsNone(done.result_id)
        done = finish_attempt(attempt.pk)
        self.assertEqual(done.result.result_points, 2)
        self.assertEqual(done.result.completed_at, attempt.deadline)
        self.assertEqual(done.result.time_spent, timedelta(minutes=10))

    def test_duplicate_finish_creates_one_result_and_one_log(self):
        attempt = start_attempt(self.student, self.test)
        with patch('solving_tests.yandex_disk.upload_test_attempt_log') as upload:
            with self.captureOnCommitCallbacks(execute=True):
                first = update_attempt(attempt.pk, 0, {'0': '4'}, finish=True)
                second = finish_attempt(attempt.pk)
            upload.assert_called_once()
        first.refresh_from_db()
        self.assertEqual(first.result_id, second.result_id)
        self.assertEqual(StudentResult.objects.count(), 1)
        self.assertTrue(first.result.is_completed)

    def test_worker_finishes_without_browser(self):
        attempt = start_attempt(self.student, self.test)
        update_attempt(attempt.pk, 0, {'0': '4'})
        with patch('solving_tests.attempts.timezone.now', return_value=attempt.deadline):
            expire_attempts()
        attempt.refresh_from_db()
        self.assertEqual(attempt.result.result_points, 2)
        self.assertEqual(start_attempt(self.student, self.test).pk, attempt.pk)

    def test_new_attempt_requires_explicit_start_and_respects_limit(self):
        first = start_attempt(self.student, self.test)
        finish_attempt(first.pk)
        self.assertEqual(start_attempt(self.student, self.test).pk, first.pk)
        second = start_attempt(self.student, self.test, new=True)
        self.assertEqual(second.attempt_number, 2)
        self.assertEqual(second.answers, [''])
        finish_attempt(second.pk)
        with self.assertRaises(PermissionError):
            start_attempt(self.student, self.test, new=True)

    def test_long_free_answer_is_not_truncated(self):
        free, _ = TypeAnswer.objects.get_or_create(type_code=5, defaults={'name': 'Free'})
        self.question.user_type = free
        self.question.user_ans = 'FREE_ANSWER'
        self.question.save()
        attempt = start_attempt(self.student, self.test)
        text = r'\text{' + 'long explanation ' * 500 + '}'
        done = update_attempt(attempt.pk, 0, {'0': text}, finish=True)
        done = finish_attempt(attempt.pk)
        self.assertEqual(json.loads(done.result.res_answer), [text])
        self.assertIsNone(done.result.free_answer_grades.get().is_correct)
        page = self.client.get(reverse('solving_tests:attempt_result', args=[self.test.name_slug_tests, attempt.pk]))
        self.assertTrue(page.context['waiting_for_review'])
        grade = done.result.free_answer_grades.get()
        grade.is_correct = True
        grade.save()
        page = self.client.get(reverse('solving_tests:attempt_result', args=[self.test.name_slug_tests, attempt.pk]))
        self.assertFalse(page.context['waiting_for_review'])
        self.assertTrue(page.context['detailed_results'][0]['is_correct'])

    def test_another_student_cannot_access_attempt_or_result(self):
        attempt = start_attempt(self.student, self.test)
        other = CustomUser.objects.create_user('other@example.com', 'pass', role='student')
        self.client.force_login(other)
        for name in ['attempt_api', 'attempt_result']:
            response = self.client.get(reverse('solving_tests:' + name, args=[self.test.name_slug_tests, attempt.pk]))
            self.assertEqual(response.status_code, 404)

    def test_invalid_payload_does_not_change_draft(self):
        attempt = start_attempt(self.student, self.test)
        for changes in [{'5': '4'}, {'0': []}, {'0': '@answers:not json'}]:
            with self.assertRaises(ValueError):
                update_attempt(attempt.pk, 0, changes)
        attempt.refresh_from_db()
        self.assertEqual(attempt.answers, [''])

    def test_result_survives_new_login_and_expired_get_does_not_start_again(self):
        attempt = start_attempt(self.student, self.test)
        with patch('solving_tests.attempts.timezone.now', return_value=attempt.deadline):
            response = self.client.get(reverse('solving_tests:some_test_for_student', args=[self.test.name_slug_tests]))
        self.assertRedirects(response, reverse('solving_tests:attempt_result', args=[self.test.name_slug_tests, attempt.pk]))
        self.client.logout()
        self.client.force_login(self.student)
        response = self.client.get(reverse('solving_tests:show_result', args=[self.test.name_slug_tests]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(TestAttempt.objects.count(), 1)

    def test_unpublished_test_cannot_create_new_attempt(self):
        self.test.is_published = 0
        self.test.save()
        with self.assertRaises(PermissionError):
            start_attempt(self.student, self.test)

    def test_local_runserver_uses_expiry_worker_wrapper(self):
        from django.core.management import get_commands
        self.assertEqual(get_commands()['runserver'], 'solving_tests')

    def test_submission_returns_before_grading_and_worker_publishes_results(self):
        attempt = start_attempt(self.student, self.test)
        api = reverse('solving_tests:attempt_api', args=[self.test.name_slug_tests, attempt.pk])
        url = reverse('solving_tests:attempt_result', args=[self.test.name_slug_tests, attempt.pk])
        with patch('solving_tests.attempts.evaluate', side_effect=AssertionError('Must not grade in submit')):
            response = self.client.post(api, json.dumps({'action': 'finish', 'revision': 0, 'changes': {'0': '4'}}), content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json()['submitted'])
            self.assertFalse(response.json()['completed'])
            self.assertTemplateUsed(self.client.get(url), 'solving_tests/submitted.html')
        submitted = TestAttempt.objects.get(pk=attempt.pk)
        update_attempt(attempt.pk, submitted.revision, {'0': '999'})
        expire_attempts()
        attempt.refresh_from_db()
        self.assertEqual(attempt.answers, ['4'])
        self.assertEqual(attempt.result.result_points, 2)
        self.assertEqual(attempt.result.completed_at, submitted.submitted_at)
        self.assertTrue(self.client.get(api).json()['completed'])
        with patch('solving_tests.attempt_views.evaluate', side_effect=AssertionError('Must reuse grades')):
            self.assertTemplateUsed(self.client.get(url), 'solving_tests/result.html')

    def test_submitted_attempt_reopens_waiting_page_and_cannot_restart(self):
        attempt = start_attempt(self.student, self.test)
        update_attempt(attempt.pk, 0, {'0': '4'}, finish=True)
        self.assertEqual(start_attempt(self.student, self.test, new=True).pk, attempt.pk)
        response = self.client.get(reverse('solving_tests:some_test_for_student', args=[self.test.name_slug_tests]))
        self.assertRedirects(response, reverse('solving_tests:attempt_result', args=[self.test.name_slug_tests, attempt.pk]))
