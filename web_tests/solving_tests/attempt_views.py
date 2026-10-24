import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from .attempts import (RevisionConflict, attempt_state, evaluate, finish_attempt,
                       start_attempt, thaw_questions, update_attempt)
from .models import TestAttempt


def student_attempt(request, test):
    try:
        attempt = start_attempt(request.user, test)
    except PermissionError:
        return redirect('solving_tests:list_test')
    if attempt.result_id:
        return redirect('solving_tests:attempt_result', slug_name=test.name_slug_tests, attempt_id=attempt.pk)
    # The browser submits through the versioned API; never create an anonymous second attempt.
    if request.method == 'POST':
        return JsonResponse({'error': 'Используйте страницу текущей попытки.'}, status=400)
    expressions = []
    from create_tests.answer_storage import split_answers
    for index, expression in enumerate(thaw_questions(attempt.questions), 1):
        expressions.append({'expression': expression, 'options': split_answers(expression['user_ans'])
            if expression['exist_select'] else [], 'exist_select': expression['exist_select'],
            'display_number': index, 'original_number': expression.get('number', index)})
    return render(request, 'solving_tests/specific_test.html', {
        'test': test, 'expressions_with_options': expressions, 'attempt': attempt,
        'attempt_state': attempt_state(attempt),
    })


@login_required
@require_POST
def new_attempt(request, slug_name):
    from create_tests.models import AboutTest
    test = get_object_or_404(AboutTest, name_slug_tests=slug_name)
    if request.user.role != 'student':
        return JsonResponse({'error': 'Доступно только студенту.'}, status=403)
    try:
        start_attempt(request.user, test, new=True)
    except PermissionError:
        return redirect('solving_tests:list_test')
    return redirect('solving_tests:some_test_for_student', slug_name=slug_name)


@login_required
@require_http_methods(['GET', 'POST'])
def attempt_api(request, slug_name, attempt_id):
    attempt = get_object_or_404(TestAttempt.objects.select_related('test'), pk=attempt_id,
                               student=request.user, test__name_slug_tests=slug_name)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            if not isinstance(data, dict) or data.get('action') not in ('save', 'finish'):
                raise ValueError
            attempt = update_attempt(attempt.pk, data.get('revision'), data.get('changes', {}),
                                     finish=data['action'] == 'finish')
        except RevisionConflict:
            attempt.refresh_from_db()
            return JsonResponse(attempt_state(attempt), status=409)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Некорректный запрос сохранения.'}, status=400)
    elif not attempt.result_id and attempt.deadline <= timezone.now():
        attempt = finish_attempt(attempt.pk)
    response = JsonResponse(attempt_state(attempt))
    response['Cache-Control'] = 'no-store'
    return response


@login_required
def attempt_result(request, slug_name, attempt_id):
    attempt = get_object_or_404(TestAttempt.objects.select_related('test', 'result'),
        pk=attempt_id, student=request.user, test__name_slug_tests=slug_name)
    if not attempt.result_id and attempt.deadline <= timezone.now():
        attempt = finish_attempt(attempt.pk)
    if not attempt.result_id:
        return redirect('solving_tests:some_test_for_student', slug_name=slug_name)
    result = attempt.result
    grades = dict(result.free_answer_grades.values_list('question_index', 'is_correct'))
    _, details = evaluate(attempt.questions, attempt.answers, grades)
    test = attempt.test
    percentage = result.percentage_score
    grade = (5 if percentage >= test.grade_5_threshold else 4 if percentage >= test.grade_4_threshold
             else 3 if percentage >= test.grade_3_threshold else 2)
    return render(request, 'solving_tests/result.html', {
        'test_name': test.name_tests, 'slug_name': slug_name, 'result': result.result_points,
        'count': result.max_points, 'score': grade, 'waiting_for_review': any(v is None for v in grades.values()),
        'result_display_mode': test.result_display_mode, 'detailed_results': details,
        'show_correct_answers': test.result_display_mode == 'show_correct',
    })
