"""Review one immutable student attempt, independently of its current ranking."""
import ast
import json

from django.shortcuts import get_object_or_404
from django.http import Http404

from .models import AboutTest


def review_test(user, slug):
    tests = AboutTest.objects.all()
    if not user.is_superuser and user.role != 'admin':
        tests = tests.filter(creator__data_map=user)
    return get_object_or_404(tests, name_slug_tests=slug)


def select_result(results, result_id=None):
    if result_id is not None:
        try:
            result_id = int(result_id)
        except (ValueError, TypeError):
            raise Http404('Unknown attempt')
        return get_object_or_404(results, pk=result_id)
    return results.order_by('-result_points', '-completed_at', '-pk').first()


def review_details(result):
    from solving_tests.attempts import evaluate, freeze_questions
    from solving_tests.models import TestAttempt
    from solving_tests.views import get_randomized_test_for_student

    attempt = TestAttempt.objects.filter(result=result).first()
    grades = dict(result.free_answer_grades.values_list('question_index', 'is_correct'))
    if attempt is not None:
        questions = attempt.questions
        answers = attempt.answers
    else:
        questions = freeze_questions(get_randomized_test_for_student(
            result.test, result.student_id, result.attempt_number))
        try:
            answers = json.loads(result.res_answer)
        except (ValueError, TypeError):
            try:
                answers = ast.literal_eval(result.res_answer)
            except (ValueError, SyntaxError, TypeError):
                answers = []
        if not isinstance(answers, list):
            answers = []

    if attempt is not None and attempt.grading_details is not None:
        details = [dict(detail) for detail in attempt.grading_details]
    else:
        _, details = evaluate(questions, answers, grades)
    for index, detail in enumerate(details):
        detail['question_index'] = index
        if detail['is_free_answer']:
            detail['is_correct'] = grades.get(index)
    return details
