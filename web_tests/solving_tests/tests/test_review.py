import json
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse

from create_tests.models import AboutExpressions, AboutTest, PublishedGroup, Subjects, TypeAnswer
from solving_tests.attempts import finish_attempt, start_attempt, update_attempt
from solving_tests.models import FreeAnswerGrade
from users.models import CustomUser, StudentData, StudentGroup, StudentInstitute, TeacherData


class AttemptReviewTests(TestCase):
    def setUp(self):
        institute = StudentInstitute.objects.create(name='Review institute')
        group = StudentGroup.objects.create(name='Review group', name_inst=institute)
        self.teacher = CustomUser.objects.create_user('review.teacher@test.local', 'pass', role='teacher')
        teacher_data = TeacherData.objects.create(data_map=self.teacher, institute=institute,
            first_name='Review', last_name='Teacher')
        self.student = CustomUser.objects.create_user('review.student@test.local', 'pass', role='student')
        StudentData.objects.create(data_map=self.student, institute=institute, group=group,
            first_name='Review', last_name='Student')
        self.test = AboutTest.objects.create(name_tests='Review test', creator=teacher_data,
            subj=Subjects.objects.create(name='Review'), is_published=1, num_of_attempts=10,
            time_to_solution=timedelta(minutes=10))
        PublishedGroup.objects.create(test_name=self.test, group_name=group, teacher_name=teacher_data)
        free, _ = TypeAnswer.objects.get_or_create(type_code=5, defaults={'name': 'Free'})
        number, _ = TypeAnswer.objects.get_or_create(type_code=1, defaults={'name': 'Number'})
        for index, kind in enumerate([free, free, number], 1):
            question = AboutExpressions.objects.create(user_expression=f'Question {index}',
                user_ans='4' if kind == number else 'FREE_ANSWER', user_type=kind,
                points_for_solve=1 if kind == number else 2, number=1, block_expression_num=index)
            self.test.expressions.add(question)
        self.client.force_login(self.teacher)

    def attempt(self, test=None):
        attempt = start_attempt(self.student, test or self.test, new=True)
        changes = {str(i): '4' if question['type_code'] == 1 else f'Response {attempt.attempt_number}/{i}'
                   for i, question in enumerate(attempt.questions)}
        update_attempt(attempt.pk, 0, changes, finish=True)
        return finish_attempt(attempt.pk)

    def pending(self):
        response = self.client.get(reverse('account2'))
        self.assertEqual(response.status_code, 200)
        ids = list(response.context['pending_results'].values_list('pk', flat=True))
        self.assertEqual(response.context['pending_results_count'], len(ids))
        return set(ids)

    def grade(self, result, index, correct, **extra):
        return self.client.post(reverse('create_tests:grade_free_answer',
            args=[self.test.name_slug_tests, self.student.pk]),
            json.dumps(dict(result_id=result.pk, question_index=index, is_correct=correct, **extra)),
            content_type='application/json')

    def test_each_pending_attempt_remains_until_its_own_questions_are_graded(self):
        first, second = self.attempt(), self.attempt()
        self.assertEqual(self.pending(), {first.result_id, second.result_id})
        first_indices = list(first.result.free_answer_grades.values_list('question_index', flat=True))
        response = self.grade(first.result, first_indices[0], True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['ungraded_count'], 1)
        self.assertEqual(self.pending(), {first.result_id, second.result_id})
        self.assertEqual(self.grade(first.result, first_indices[1], False).status_code, 200)
        self.assertEqual(self.pending(), {second.result_id})
        self.assertEqual(second.result.free_answer_grades.filter(is_correct__isnull=True).count(), 2)
        self.assertEqual(self.grade(first.result, first_indices[1], None).status_code, 200)
        self.assertEqual(self.pending(), {first.result_id, second.result_id})

    def test_reviewed_best_result_cannot_hide_a_new_submission(self):
        old = self.attempt()
        for index in old.result.free_answer_grades.values_list('question_index', flat=True):
            self.grade(old.result, index, True)
        new = self.attempt()
        self.assertEqual(self.pending(), {new.result_id})
        page = self.client.get(reverse('account2'))
        self.assertContains(page, f'?result_id={new.result_id}')

    def test_grading_one_test_leaves_other_tests_in_the_queue(self):
        first = self.attempt()
        other = AboutTest.objects.create(name_tests='Other review test', creator=self.test.creator,
            subj=self.test.subj, is_published=1, num_of_attempts=10,
            time_to_solution=timedelta(minutes=10))
        other.expressions.set(self.test.expressions.all())
        PublishedGroup.objects.create(test_name=other, group_name=self.student.studentdata.group,
                                      teacher_name=self.test.creator)
        remaining = self.attempt(other)
        for index in first.result.free_answer_grades.values_list('question_index', flat=True):
            self.grade(first.result, index, True)
        self.assertEqual(self.pending(), {remaining.result_id})

    def test_review_page_and_repeated_posts_stay_on_the_selected_attempt(self):
        first, second = self.attempt(), self.attempt()
        indices = list(first.result.free_answer_grades.values_list('question_index', flat=True))
        url = reverse('create_tests:test_results_detail', args=[self.test.name_slug_tests, self.student.pk])
        page = self.client.get(url, {'result_id': first.result_id})
        self.assertEqual(page.context['best_result'].pk, first.result_id)
        self.assertContains(page, f'data-result-id="{first.result_id}"')
        self.grade(first.result, indices[0], True)
        self.grade(second.result, indices[0], True)
        self.grade(second.result, indices[1], True)
        self.grade(first.result, indices[1], False)
        self.assertIs(first.result.free_answer_grades.get(question_index=indices[1]).is_correct, False)
        self.assertIs(second.result.free_answer_grades.get(question_index=indices[1]).is_correct, True)

    def test_review_uses_frozen_questions_and_cached_automatic_scores(self):
        attempt = self.attempt()
        index = attempt.result.free_answer_grades.first().question_index
        question = attempt.questions[index]['user_expression']
        self.test.expressions.clear()
        self.assertEqual(self.pending(), {attempt.result_id})
        url = reverse('create_tests:test_results_detail', args=[self.test.name_slug_tests, self.student.pk])
        page = self.client.get(url, {'result_id': attempt.result_id})
        self.assertEqual(page.context['detailed_results'][index]['question'], question)
        self.assertEqual(self.grade(attempt.result, index, True).json()['new_score'], 3)
        attempt.result.refresh_from_db()
        self.assertEqual(attempt.result.percentage_score, 60)

    def test_invalid_or_ambiguous_grading_does_not_change_any_result(self):
        attempt = self.attempt()
        self.attempt()
        index = attempt.result.free_answer_grades.first().question_index
        url = reverse('create_tests:grade_free_answer', args=[self.test.name_slug_tests, self.student.pk])
        for body in [dict(question_index=index, is_correct=True),
                     dict(result_id=attempt.result_id, question_index=True, is_correct=True),
                     dict(result_id=attempt.result_id, question_index=index, is_correct='false'),
                     dict(result_id=attempt.result_id, question_index=-1, is_correct=True),
                     dict(result_id=attempt.result_id, question_index=100, is_correct=True)]:
            self.assertEqual(self.client.post(url, json.dumps(body), content_type='application/json').status_code, 400)
        automatic = next(i for i, q in enumerate(attempt.questions) if q['type_code'] == 1)
        self.assertEqual(self.grade(attempt.result, automatic, True).status_code, 400)
        self.assertFalse(FreeAnswerGrade.objects.filter(is_correct__isnull=False).exists())

    def test_another_teacher_cannot_view_or_grade_this_work(self):
        attempt = self.attempt()
        other = CustomUser.objects.create_user('other.teacher@test.local', 'pass', role='teacher')
        self.client.force_login(other)
        for name, args in [('test_results_list', [self.test.name_slug_tests]),
                           ('test_results_detail', [self.test.name_slug_tests, self.student.pk])]:
            self.assertEqual(self.client.get(reverse('create_tests:' + name, args=args)).status_code, 404)
        self.assertEqual(self.grade(attempt.result, attempt.result.free_answer_grades.first().question_index, True).status_code, 404)
