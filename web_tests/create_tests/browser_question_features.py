"""Explicit real-browser verification of editor saving, images and matrix scaffolds."""
import io
import os
from pathlib import Path
from unittest.mock import patch

from PIL import Image
from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings
from django.urls import path, include, re_path, reverse
from django.views.static import serve

from .test_question_images import QuestionFeaturesTests
from .models import AboutTest, QuestionImage, TypeAnswer
from solving_tests.models import TestAttempt


def test_media(request, path):
    return serve(request, path, document_root=settings.MEDIA_ROOT)


urlpatterns = [path('', include('web_tests.urls')), re_path(r'^media/(?P<path>.*)$', test_media)]


@override_settings(ROOT_URLCONF='create_tests.browser_question_features')
class QuestionFeaturesBrowserAudit(StaticLiveServerTestCase):
    def setUp(self):
        QuestionFeaturesTests.setUp(self)
        guard = patch.dict(os.environ, {'DJANGO_ALLOW_ASYNC_UNSAFE': 'true'})
        guard.start()
        self.addCleanup(guard.stop)
        from playwright.sync_api import sync_playwright
        self.playwright = sync_playwright().start()
        self.addCleanup(self.playwright.stop)
        self.browser = self.playwright.chromium.launch(channel='chrome', headless=True)
        self.addCleanup(self.browser.close)
        self.context = self.browser.new_context(viewport={'width': 1280, 'height': 900})
        self.addCleanup(self.context.close)
        # Do not intercept local multipart uploads: older Playwright versions
        # truncate binary upload bodies when continuing intercepted requests.
        self.context.route('https://**/*', lambda route: route.abort())
        # Match the existing visual regression pages: optional speech modules
        # are absent from the bundled MathJax build and are outside this audit.
        macros = (Path(settings.BASE_DIR)/'static/js/macros-mathJax.js').read_text(encoding='utf-8')
        macros += '\nMathJax.options = {enableMenu:false, enableExplorer:false, enableEnrichment:false, enableSpeech:false, enableBraille:false, renderActions:{enrich:[],attachSpeech:[],addMenu:[],explorable:[]}};'
        self.context.route('**/macros-mathJax.js', lambda route: route.fulfill(body=macros, content_type='application/javascript'))
        self.page = self.context.new_page()
        self.page.set_default_timeout(15000)
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.login(self.teacher)

    def login(self, user):
        self.client.force_login(user)
        self.context.clear_cookies()
        self.context.add_cookies([{'name': settings.SESSION_COOKIE_NAME,
            'value': self.client.cookies[settings.SESSION_COOKIE_NAME].value, 'url': self.live_server_url}])

    def test_create_continue_edit_images_and_student_matrix(self):
        self.page.goto(self.live_server_url + reverse('create_tests:create_test'))
        self.page.wait_for_function("window.QuestionImages && customElements.get('math-field') && document.querySelector('.question-images-editor')")
        self.page.wait_for_timeout(1100)  # Existing delayed draft restoration.
        self.page.locator('math-field[name="user_expression"]').evaluate("el => el.value = '2+2'")
        self.page.locator('.answer-field').evaluate("el => el.value = '4'")
        self.page.locator('.type-field').select_option(str(self.question.user_type_id))
        self.page.locator('[name="group_points"]').fill('2')
        buffer = io.BytesIO()
        image = Image.new('RGB', (640, 280), '#edf3fa')
        from PIL import ImageDraw
        draw = ImageDraw.Draw(image)
        draw.line((80, 140, 560, 140), fill='#4a6fa5', width=5)
        draw.ellipse((270, 90, 370, 190), outline='#4a6fa5', width=5)
        image.save(buffer, format='PNG')
        with self.page.expect_response('**/upload-question-image/') as upload_response:
            self.page.locator('.question-image-upload input').set_input_files({
                'name': 'diagram.png', 'mimeType': 'image/png', 'buffer': buffer.getvalue(),
            })
        self.assertEqual(upload_response.value.status, 201, upload_response.value.text())
        self.page.wait_for_selector('.question-image-row')
        self.page.locator('.question-image-caption').fill('Figure 1. Diagram')
        self.page.locator('.save-btn').first.click()
        self.page.locator('#testNameInput').fill('Browser images test')
        self.page.locator('#subj_test').select_option(str(self.test.subj_id))
        self.page.locator('#num_attempts').fill('2')
        self.page.locator('#hours').fill('0')
        self.page.locator('#minutes').fill('10')
        with self.page.expect_navigation():
            self.page.locator('.save-and-continue').click()
        self.assertIn('/edit-test/', self.page.url)
        self.page.wait_for_selector('.question-image-row')
        created = AboutTest.objects.get(name_tests='Browser images test')
        self.assertEqual(created.expressions.get().images.count(), 1)
        self.assertEqual(self.page.locator('.question-image-caption').input_value(), 'Figure 1. Diagram')
        self.page.locator('math-field[name="user_expression"]').evaluate("el => el.value = '2+3'")
        self.page.locator('.answer-field').evaluate("el => el.value = '5'")
        self.page.locator('.save-btn').first.click()
        with self.page.expect_navigation():
            self.page.locator('.save-and-continue').click()
        self.page.wait_for_selector('.question-image-row')
        self.assertEqual(created.expressions.get().user_expression, '2+3')
        self.assertEqual(AboutTest.objects.filter(name_tests='Browser images test').count(), 1)
        screenshots = Path(settings.BASE_DIR).parent / 'backups'
        screenshots.mkdir(exist_ok=True)
        self.page.screenshot(path=str(screenshots/'question-features-editor.png'), full_page=True)
        self.page.locator('.save-btn').first.click()
        self.page.wait_for_timeout(400)  # Let the modal's opacity animation finish for visual QA.
        self.page.screenshot(path=str(screenshots/'question-features-save.png'), full_page=True)
        self.page.locator('.close-modal').click()
        self.page.locator('#add-task-group').click()
        self.page.wait_for_function("document.querySelectorAll('.question-images-editor').length === 2")
        self.assertEqual(self.page.locator('.question-image-row').count(), 1, 'Cloning a new task must not copy images')

        matrix, _ = TypeAnswer.objects.get_or_create(type_code=4, defaults={'name': 'Matrix'})
        self.question.user_type = matrix
        self.question.user_ans = r'\begin{pmatrix}7&8\\9&10\end{pmatrix}'
        self.question.save()
        self.question.images.add(QuestionImage.objects.get())
        self.login(self.student)
        self.page.goto(self.live_server_url + reverse('solving_tests:some_test_for_student', args=[self.test.name_slug_tests]))
        self.page.wait_for_function("document.querySelector('math-field').value.includes('pmatrix')")
        self.page.wait_for_function("document.querySelector('.question-illustration img').naturalWidth > 0")
        self.page.evaluate('async () => { await window.MathJax?.startup?.promise; await document.fonts.ready; }')
        self.assertEqual(self.page.locator('math-field').evaluate('el => studentFieldAnswer(el)'), '')
        self.assertFalse(self.page.locator('#nav-1').evaluate("el => el.classList.contains('completed')"))
        self.assertEqual(TestAttempt.objects.get(student=self.student).answers, [''])
        self.page.screenshot(path=str(screenshots/'question-features-student.png'), full_page=True)
        self.page.locator('math-field').evaluate("""(el, value) => {
            el.value = value;
            el.dispatchEvent(new Event('input', {bubbles: true}));
        }""", r'\begin{pmatrix}7&8\\9&10\end{pmatrix}')
        self.page.wait_for_function("document.getElementById('saveStatus').textContent.includes('\u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u044b')")
        self.page.reload()
        self.page.wait_for_function("document.querySelector('math-field').value.includes('10')")
        self.assertEqual(self.page.locator('.question-illustration').count(), 1)
        self.assertEqual(self.errors, [])
