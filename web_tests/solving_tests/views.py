import json
from django.contrib.auth import logout
from django.shortcuts import render, get_object_or_404, redirect
from create_tests.models import AboutExpressions, AboutTest, PublishedGroup
from users.models import StudentGroup, StudentData
from .models import StudentResult
from logic_of_expression.check_sympy_expr import CheckAnswer
import numpy as np
from .decorators import role_required
from django.contrib.auth.decorators import login_required
from django.db.models import Sum


@login_required
@role_required(['student', 'admin'])
def list_test(request):
    user = request.user

    try:
        student = StudentData.objects.get(data_map=user)
        student_group = student.group
        all_tests = AboutTest.objects.filter(publishedgroup__group_name=student_group).distinct()

        tests_with_attempts = []
        for test in all_tests:
            attempts = StudentResult.objects.filter(student=user, test=test).count()
            if attempts < test.num_of_attempts:
                tests_with_attempts.append({
                    'test': test,
                    'remaining_attempts': test.num_of_attempts - attempts
                })

    except StudentData.DoesNotExist:
        tests_with_attempts = []

    return render(request, 'solving_tests/test_selection.html', {
        'tests': tests_with_attempts
    })


@login_required
@role_required(['student', 'admin'])
def some_test_for_student(request, slug_name):
    test = get_object_or_404(AboutTest, name_slug_tests=slug_name)
    student = request.user

    attempt_count = StudentResult.objects.filter(student=student, test=test).count()
    if attempt_count >= test.num_of_attempts:
        return redirect('solving_tests:show_result', slug_name=slug_name)

    if request.method == 'POST':
        raw = request.POST.get('binaryAnswers', '[]')
        try:
            student_answers = json.loads(raw)
        except json.JSONDecodeError:
            student_answers = []

        expressions = list(test.expressions.all())
        n = len(expressions)
        if len(student_answers) < n:
            student_answers += [''] * (n - len(student_answers))
        elif len(student_answers) > n:
            student_answers = student_answers[:n]

        right_answers = [ex.user_ans for ex in expressions]
        is_choice = [ex.exist_select for ex in expressions]
        var_true_ans = [ex.true_ans for ex in expressions]
        points = [ex.points_for_solve for ex in expressions]
        all_p = np.sum(points)

        result_score = 0
        for i, ex in enumerate(expressions):
            user_ans = student_answers[i]
            if is_choice[i]:
                ua = ''.join(user_ans)
                va = var_true_ans[i].replace(';', '')
                res = CheckAnswer(va, ua, True).compare_answer()
            else:
                res = CheckAnswer(right_answers[i], user_ans, False).compare_answer()
            result_score += res * points[i]

        score_in_pr = result_score / all_p * 100
        if score_in_pr >= 80:
            grade = 5
        elif score_in_pr >= 60:
            grade = 4
        elif score_in_pr >= 35:
            grade = 3
        else:
            grade = 2

        request.session['test_result'] = {
            'result': result_score,
            'score': grade,
            'test_name': test.name_tests,
        }

        StudentResult.objects.create(
            student=student,
            test=test,
            attempt_number=attempt_count + 1,
            result_points=result_score,
            res_answer=str(student_answers),
        )

        return redirect('solving_tests:show_result', slug_name=slug_name)

    expressions_with_options = []
    for ex in test.expressions.all():
        options = ex.user_ans.split(';') if ex.user_ans else []
        expressions_with_options.append({
            'expression': ex,
            'options': options,
            'exist_select': ex.exist_select,
        })

    return render(request, 'solving_tests/specific_test.html', {
        'test': test,
        'expressions_with_options': expressions_with_options,
    })


@login_required
@role_required(['student', 'admin'])
def show_result(request, slug_name):
    test_result = request.session.get('test_result')

    if not test_result:
        return redirect('list_test')

    test = AboutTest.objects.get(name_slug_tests=slug_name)
    count = test.expressions.aggregate(Sum('points_for_solve'))['points_for_solve__sum'] or 0

    return render(request, 'solving_tests/result.html', {
        'test_name': test_result['test_name'],
        'result': test_result['result'],
        'score': test_result['score'],
        'count': count,
        'slug_name': slug_name,
    })


@login_required
@role_required(['student', 'admin'])
def finished_tests(request):
    user = request.user
    finished = []

    try:
        student = StudentData.objects.get(data_map=user)
        student_group = student.group
        all_tests = AboutTest.objects.filter(publishedgroup__group_name=student_group).distinct()

        for test in all_tests:
            attempts = StudentResult.objects.filter(student=user, test=test).count()
            if attempts >= test.num_of_attempts:
                finished.append(test)

    except StudentData.DoesNotExist:
        pass

    return render(request, 'solving_tests/finished_tests.html', {
        'finished_tests': finished
    })
