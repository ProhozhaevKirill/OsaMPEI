import io
import json
import tempfile

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from solving_tests.attempts import start_attempt, finish_attempt
from solving_tests.tests import test_attempts
from users.models import CustomUser
from .models import AboutTest, QuestionImage, TypeAnswer


class QuestionFeaturesTests(TestCase):
    def setUp(self):
        test_attempts.AttemptTests.setUp(self)
        self.teacher = self.test.creator.data_map
        self.client.force_login(self.teacher)
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        override = override_settings(MEDIA_ROOT=folder.name, YANDEX_DISK_TOKEN='')
        override.enable()
        self.addCleanup(override.disable)

    def upload(self):
        data = io.BytesIO()
        Image.new('RGB', (24, 16), '#4a6fa5').save(data, format='PNG')
        return self.client.post(reverse('create_tests:upload_question_image'), {
            'image': SimpleUploadedFile('diagram.png', data.getvalue(), content_type='image/png'),
        })

    def payload(self, image=None):
        payload = {
            'name_test': 'With illustrations', 'time_solve': '00:10:00', 'num_attempts': 2,
            'subj_test': self.test.subj_id, 'save_action': 'continue',
            'user_expression': json.dumps(['Find the answer']), 'user_ans': json.dumps(['4']),
            'user_bool_ans': json.dumps(['1']), 'user_eps': json.dumps(['0']),
            'user_type': json.dumps([self.question.user_type_id]), 'point_solve': json.dumps([2]),
            'user_norm': json.dumps(['']), 'number': json.dumps([1]),
            'block_expression_num': json.dumps([1]),
        }
        if image:
            payload['question_images'] = json.dumps([[{'id': image['id'], 'caption': 'Figure <1>'}]])
        return payload

    def test_save_continue_actually_saves_create_and_edit_with_images(self):
        uploaded = self.upload()
        self.assertEqual(uploaded.status_code, 201)
        payload = self.payload(uploaded.json())
        response = self.client.post(reverse('create_tests:create_test'), payload)
        test = AboutTest.objects.get(name_tests='With illustrations')
        editor = reverse('create_tests:edit_test', args=[test.name_slug_tests])
        self.assertRedirects(response, editor)
        self.assertEqual(test.expressions.get().images.get().caption, 'Figure <1>')
        response = self.client.post(editor, payload)
        self.assertRedirects(response, editor)
        self.assertEqual(AboutTest.objects.filter(name_tests='With illustrations').count(), 1)
        self.assertEqual(test.expressions.get().images.get().pk, uploaded.json()['id'])
        payload['save_action'] = 'list'
        response = self.client.post(editor, payload)
        self.assertRedirects(response, reverse('create_tests:test_list'))

    def test_new_format_edit_preserves_illustrations(self):
        image = self.upload().json()
        payload = self.payload(image)
        payload['task_groups_data'] = json.dumps([{'points': 2, 'variants': [{
            'expression': 'Find the answer', 'answers': ['4'], 'epsilons': ['0'],
            'boolAnswers': ['1'], 'types': self.question.user_type_id,
        }]}])
        response = self.client.post(reverse('create_tests:edit_test', args=[self.test.name_slug_tests]), payload)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.test.task_groups.get().variants.get().images.get().pk, image['id'])

    def test_cannot_attach_another_teachers_image(self):
        image = QuestionImage.objects.get(pk=self.upload().json()['id'])
        other = CustomUser.objects.create_user('image.other@example.com', 'pass', role='teacher')
        image.uploader = other
        image.save()
        response = self.client.post(reverse('create_tests:create_test'), self.payload({'id': image.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(AboutTest.objects.filter(name_tests='With illustrations').exists())

    def test_rejects_non_image_and_student_upload(self):
        response = self.client.post(reverse('create_tests:upload_question_image'), {
            'image': SimpleUploadedFile('diagram.svg', b'<svg/>', content_type='image/svg+xml'),
        })
        self.assertEqual(response.status_code, 400)
        self.assertFalse(QuestionImage.objects.exists())
        self.client.force_login(self.student)
        self.assertEqual(self.upload().status_code, 403)

    def test_rejects_oversized_file_and_wrong_attachment_count(self):
        response = self.client.post(reverse('create_tests:upload_question_image'), {
            'image': SimpleUploadedFile('large.png', b'x' * (5 * 1024 * 1024 + 1), content_type='image/png'),
        })
        self.assertEqual(response.status_code, 400)
        payload = self.payload()
        payload['question_images'] = '[]'
        response = self.client.post(reverse('create_tests:create_test'), payload)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(AboutTest.objects.filter(name_tests='With illustrations').exists())

    def test_other_teacher_cannot_edit_test_or_its_images(self):
        other = CustomUser.objects.create_user('editor.other@example.com', 'pass', role='teacher')
        self.client.force_login(other)
        response = self.client.post(reverse('create_tests:edit_test', args=[self.test.name_slug_tests]), self.payload())
        self.assertEqual(response.status_code, 403)
        self.assertTrue(self.test.expressions.filter(pk=self.question.pk).exists())

    def test_attempt_freezes_images_and_matrix_scaffold_without_answer_values(self):
        image = QuestionImage.objects.get(pk=self.upload().json()['id'])
        image.caption = 'Original diagram'
        image.save()
        matrix, _ = TypeAnswer.objects.get_or_create(type_code=4, defaults={'name': 'Matrix'})
        self.question.user_type = matrix
        self.question.user_ans = r'\begin{pmatrix}78421&2\\3&4\end{pmatrix}'
        self.question.save()
        self.question.images.add(image)
        attempt = start_attempt(self.student, self.test)
        self.question.images.clear()
        image.caption = 'Changed diagram'
        image.save()
        self.client.force_login(self.student)
        response = self.client.get(reverse('solving_tests:some_test_for_student', args=[self.test.name_slug_tests]))
        self.assertContains(response, 'Original diagram')
        self.assertContains(response, 'data-answer-template=')
        self.assertContains(response, r'\placeholder{}')
        self.assertNotContains(response, '78421')
        done = finish_attempt(attempt.pk)
        self.assertEqual(done.grading_details[0]['images'][0]['caption'], 'Original diagram')
        self.assertEqual(done.result.result_points, 0)
