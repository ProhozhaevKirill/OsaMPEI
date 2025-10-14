import json
import random
from django.contrib.auth import logout
from django.shortcuts import render, get_object_or_404, redirect
from create_tests.models import AboutExpressions, AboutTest, PublishedGroup, TypeNormForMatrix
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


def get_randomized_test_for_student(test, student_id, attempt_number=1):
    """
    Генерирует рандомизированный вариант теста для студента
    На основе student_id, test_id и attempt_number создается seed для генератора случайных чисел
    чтобы каждая попытка давала уникальный вариант

    Логика рандомизации:
    - Группируем задания по block_expression_num
    - Из каждого блока выбираем случайное задание для студента
    - Сортируем по полю number для правильного порядка отображения
    - Каждая попытка генерирует новый вариант
    """
    # Создаем seed на основе id студента, id теста и номера попытки
    seed = hash(f"{student_id}_{test.id}_{attempt_number}") % (2**32)
    random.seed(seed)

    randomized_expressions = []

    # Группируем задания по блокам
    from collections import defaultdict
    blocks = defaultdict(list)

    for ex in test.expressions.all():
        blocks[ex.block_expression_num].append(ex)

    # Из каждого блока выбираем случайное задание
    selected_expressions = []
    for block_num, expressions in blocks.items():
        if expressions:
            # Выбираем случайное задание из блока
            selected_expression = random.choice(expressions)
            selected_expressions.append(selected_expression)

    # Сортируем по полю number для правильного порядка
    selected_expressions.sort(key=lambda x: x.number)

    # Формируем окончательный список
    for ex in selected_expressions:
        norm_for_matrix = TypeNormForMatrix.objects.filter(num_expr=ex).first()
        randomized_expressions.append({
            'user_expression': ex.user_expression,
            'user_ans': ex.user_ans,
            'true_ans': ex.true_ans,
            'user_eps': ex.user_eps,
            'user_type': ex.user_type,
            'points_for_solve': ex.points_for_solve,
            'exist_select': ex.exist_select,
            'matrix_norm': norm_for_matrix.matrix_norms if norm_for_matrix else None,
            'number': ex.number,
            'block_expression_num': ex.block_expression_num
        })

    return randomized_expressions


@login_required
@role_required(['student', 'admin'])
def some_test_for_student(request, slug_name):
    test = get_object_or_404(AboutTest, name_slug_tests=slug_name)
    student = request.user

    attempt_count = StudentResult.objects.filter(student=student, test=test).count()
    if attempt_count >= test.num_of_attempts:
        return redirect('solving_tests:show_result', slug_name=slug_name)

    # Получаем рандомизированный вариант теста для студента
    # Номер попытки = количество уже выполненных попыток + 1
    expressions_data = get_randomized_test_for_student(test, student.id, attempt_count + 1)

    if request.method == 'POST':
        raw = request.POST.get('binaryAnswers', '[]')
        try:
            student_answers = json.loads(raw)
        except json.JSONDecodeError:
            student_answers = []

        n = len(expressions_data)
        if len(student_answers) < n:
            student_answers += [''] * (n - len(student_answers))
        elif len(student_answers) > n:
            student_answers = student_answers[:n]

        result_score = 0
        all_points = sum(expr['points_for_solve'] for expr in expressions_data)

        for i, expr_data in enumerate(expressions_data):
            user_ans = student_answers[i]

            if expr_data['exist_select']:
                # Multiple choice question
                ua = ''.join(user_ans)
                va = expr_data['true_ans'].replace(';', '')
                res = CheckAnswer(va, ua, True, type_ans=expr_data['user_type'].type_code).compare_answer()
            else:
                # Single answer question
                if expr_data['user_type'].type_code == 4:  # Matrix type
                    if expr_data['matrix_norm']:
                        res = CheckAnswer(expr_data['user_ans'], user_ans, False,
                                        expression=expr_data['user_expression'],
                                        type_ans=expr_data['user_type'].type_code,
                                        type_norm=expr_data['matrix_norm']).compare_answer()
                    else:
                        res = CheckAnswer(expr_data['user_ans'], user_ans, False,
                                        expression=expr_data['user_expression'],
                                        type_ans=expr_data['user_type'].type_code).compare_answer()
                else:
                    res = CheckAnswer(expr_data['user_ans'], user_ans, False,
                                    expression=expr_data['user_expression'],
                                    type_ans=expr_data['user_type'].type_code).compare_answer()

            result_score += res * expr_data['points_for_solve']

        score_in_pr = result_score / all_points * 100 if all_points > 0 else 0

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

    # Подготавливаем данные для отображения
    expressions_with_options = []
    for i, expr_data in enumerate(expressions_data):
        options = expr_data['user_ans'].split(';') if expr_data['user_ans'] else []
        expressions_with_options.append({
            'expression': expr_data,
            'options': options,
            'exist_select': expr_data['exist_select'],
            'display_number': i + 1,  # Номер для отображения (порядковый)
            'original_number': expr_data.get('number', i + 1)  # Оригинальный номер из БД
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

    # Подсчитываем общее количество баллов (используем старую систему)
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
