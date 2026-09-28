import json
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TestCase, SimpleTestCase

from .answer_storage import pack_answers, split_answers
from .models import AboutExpressions, AboutTest, Subjects, TaskGroup, TaskVariant, TypeAnswer
from .views import create_test, edit_test
from logic_of_expression.matrix import MasterMatrix


class AnswerStorageTests(SimpleTestCase):
    def test_choices_with_spaces_and_semicolons(self):
        answers = [r'first\;answer', 'text; with; punctuation', r'\begin{pmatrix}1&2\\3&4\end{pmatrix}']
        self.assertEqual(split_answers(pack_answers(answers)), answers)
        self.assertEqual(split_answers(r'first\;answer;second'), [r'first\;answer', 'second'])

    def test_matrix_formats_and_invalid_input(self):
        expected = r'\begin{pmatrix}1&2\\3&4\end{pmatrix}'
        for env in ['matrix', 'pmatrix', 'bmatrix', 'Bmatrix', 'vmatrix', 'Vmatrix', 'smallmatrix']:
            with self.subTest(env=env):
                actual = r'\begin{' + env + r'}1&2\\3&4\\\end{' + env + '}'
                self.assertTrue(MasterMatrix('', expected, actual).get_result())
        for invalid in ['', 'nonsense', r'\begin{pmatrix}1&2\\3\end{pmatrix}']:
            self.assertFalse(MasterMatrix('', invalid, invalid).get_result())

    def test_matrix_norm_model_and_fraction(self):
        norm = SimpleNamespace(type_code=1)
        self.assertTrue(MasterMatrix('', r'\begin{bmatrix}\frac{1}{2}\end{bmatrix}',
                                     r'\begin{matrix}0.51\end{matrix}', norm, 0.02).get_result())
        self.assertFalse(MasterMatrix('', r'\begin{matrix}1\end{matrix}',
                                      r'\begin{matrix}1&1\end{matrix}', norm, 0.02).get_result())


class EditorSaveTests(TestCase):
    def setUp(self):
        self.subject = Subjects.objects.create(name='Regression subject')
        self.kind, _ = TypeAnswer.objects.get_or_create(type_code=1, defaults={'name': 'Number'})
        self.test = AboutTest.objects.create(name_tests='Regression test', subj=self.subject)
        self.original = AboutExpressions.objects.create(user_expression='Original', user_ans='1', user_type=self.kind)
        self.test.expressions.add(self.original)
        self.factory = RequestFactory()

    def request(self, method, data=None):
        request = getattr(self.factory, method)('/', data=data or {})
        request.user = SimpleNamespace(is_authenticated=True, is_superuser=True, role='teacher')
        request.session = {}
        request._messages = FallbackStorage(request)
        return request

    def payload(self, answers=None):
        answers = answers or ['1', r'long\;answer;with punctuation' * 30]
        fields = {
            'user_expression': ['Question one', 'Question two'],
            'user_ans': answers, 'user_bool_ans': ['1', '1'],
            'user_eps': ['0', '0'], 'user_type': [self.kind.pk, self.kind.pk],
            'point_solve': [1, 2], 'user_norm': ['', ''],
            'number': [1, 1], 'block_expression_num': [1, 2],
        }
        return {key: json.dumps(value) for key, value in fields.items()}

    def editor_context(self):
        with patch('create_tests.views.render', side_effect=lambda request, template, context: context):
            return edit_test(self.request('get'), self.test.name_slug_tests)

    def test_save_reopen_preserves_long_single_answer_and_questions(self):
        payload = self.payload()
        response = edit_test(self.request('post', payload), self.test.name_slug_tests)
        self.assertEqual(response.status_code, 302)
        groups = self.editor_context()['task_groups_data']
        self.assertEqual(len(groups), 2)
        answers = groups[1]['variants'][0]['answers']
        self.assertEqual(len(answers), 1)
        self.assertEqual(answers[0]['user_ans'], json.loads(payload['user_ans'])[1])

    def test_choice_roundtrip(self):
        payload = self.payload([pack_answers(['a;b', r'c\;d']), '2'])
        payload['user_bool_ans'] = json.dumps(['1;0', '1'])
        payload['user_eps'] = json.dumps(['0;0', '0'])
        edit_test(self.request('post', payload), self.test.name_slug_tests)
        answers = self.editor_context()['task_groups_data'][0]['variants'][0]['answers']
        self.assertEqual([a['user_ans'] for a in answers], ['a;b', r'c\;d'])

    def test_failed_save_restores_original_rows(self):
        payload = self.payload()
        payload['point_solve'] = json.dumps([1, 'invalid'])
        edit_test(self.request('post', payload), self.test.name_slug_tests)
        self.assertEqual(list(self.test.expressions.values_list('pk', flat=True)), [self.original.pk])
        self.assertEqual(AboutExpressions.objects.count(), 1)

    def test_missing_arrays_do_not_truncate_questions(self):
        payload = self.payload()
        payload['user_type'] = json.dumps([self.kind.pk])
        edit_test(self.request('post', payload), self.test.name_slug_tests)
        self.assertTrue(self.test.expressions.filter(pk=self.original.pk).exists())

    def test_task_group_storage_is_visible_in_editor(self):
        self.test.expressions.clear()
        group = TaskGroup.objects.create(number=1)
        self.test.task_groups.add(group)
        TaskVariant.objects.create(task_group=group, user_expression='Grouped question', user_ans='1', user_type=self.kind)
        groups = self.editor_context()['task_groups_data']
        self.assertEqual(groups[0]['variants'][0]['user_expression'], 'Grouped question')

    def test_invalid_type_rolls_back_all_variants(self):
        payload = self.payload()
        payload['user_type'] = json.dumps([self.kind.pk, 999999])
        edit_test(self.request('post', payload), self.test.name_slug_tests)
        self.assertEqual(list(self.test.expressions.values_list('pk', flat=True)), [self.original.pk])

    def test_create_failure_rolls_back_and_renders_error(self):
        payload = self.payload()
        payload.update(name_test='New test', time_solve='01:00:00', num_attempts='1', subj_test=self.subject.pk)
        payload['point_solve'] = json.dumps([1, 'invalid'])
        with patch('create_tests.views.TeacherData.objects.get', return_value=None):
            response = create_test(self.request('post', payload))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(AboutTest.objects.count(), 1)
        self.assertEqual(AboutExpressions.objects.count(), 1)

    def test_create_preserves_multiple_variants(self):
        payload = self.payload()
        payload.update(name_test='New test', time_solve='01:00:00', num_attempts='1', subj_test=self.subject.pk)
        payload['block_expression_num'] = json.dumps([1, 1])
        payload['number'] = json.dumps([1, 2])
        with patch('create_tests.views.TeacherData.objects.get', return_value=None):
            response = create_test(self.request('post', payload))
        self.assertEqual(response.status_code, 302)
        created = AboutTest.objects.get(name_tests='New test')
        self.assertEqual(list(created.expressions.order_by('number').values_list('number', flat=True)), [1, 2])
