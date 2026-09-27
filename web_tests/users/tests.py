from unittest.mock import patch

from django.test import TestCase, SimpleTestCase, override_settings
from django.urls import get_resolver

from .models import CustomUser, StudentInstitute, TeacherData, WhiteList


class TeacherRegistrationTests(TestCase):
    def setUp(self):
        self.institute = StudentInstitute.objects.create(name='Test institute')
        WhiteList.objects.create(teacher_mail='krymovny@mpei.ru')

    def start_registration(self):
        return self.client.post('/register/', {
            'email': 'KrymovNY@mpei.ru',
            'password1': 'Test-password-123',
            'password2': 'Test-password-123',
        })

    def test_teacher_can_complete_registration(self):
        response = self.start_registration()
        self.assertTemplateUsed(response, 'users/teacher_registration.html')
        self.assertContains(response, 'action="/form_registration_teacher/"')
        self.assertFalse(CustomUser.objects.exists())
        response = self.client.post('/form_registration_teacher/', {
            'first_name': 'Test', 'last_name': 'Teacher',
            'institute': self.institute.pk,
        })
        self.assertRedirects(response, '/TestsCreate/listTests/', fetch_redirect_response=False)
        user = CustomUser.objects.get(email='krymovny@mpei.ru')
        self.assertEqual(user.role, 'teacher')
        self.assertTrue(user.check_password('Test-password-123'))
        self.assertTrue(TeacherData.objects.filter(data_map=user).exists())
        self.assertNotIn('pending_registration', self.client.session)

    def test_pending_registration_and_invalid_profile_render(self):
        self.start_registration()
        self.assertTemplateUsed(self.start_registration(), 'users/teacher_registration.html')
        for payload in ({}, {'first_name': 'Test', 'last_name': 'Teacher', 'institute': 999999}):
            response = self.client.post('/form_registration_teacher/', payload)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'users/teacher_registration.html')
        self.assertFalse(CustomUser.objects.exists())

    def test_student_registration_still_renders(self):
        WhiteList.objects.all().delete()
        self.assertTemplateUsed(self.start_registration(), 'users/reg_form_student.html')


@override_settings(DEBUG=False)
class ProductionErrorTests(SimpleTestCase):
    def test_error_handlers_registered(self):
        for status in (403, 404, 500):
            self.assertEqual(get_resolver().resolve_error_handler(status).__module__, 'users.error_handlers')

    def test_404_page(self):
        response = self.client.get('/missing-page/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'errors/404.html')

    def test_500_page_hides_exception(self):
        self.client.raise_request_exception = False
        with patch('users.views.SignUpForm', side_effect=RuntimeError('private-error-details')):
            response = self.client.get('/register/')
        self.assertEqual(response.status_code, 500)
        self.assertTemplateUsed(response, 'errors/500.html')
        self.assertNotContains(response, 'private-error-details', status_code=500)
