import json
import logging
import random
from django.contrib.auth import logout
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from create_tests.models import AboutExpressions, AboutTest, PublishedGroup, TypeNormForMatrix
from users.models import StudentGroup, StudentData, TeacherData
from .models import StudentResult, StudentTaskAnswer
from logic_of_expression.check_sympy_expr import CheckAnswer
import numpy as np
from .decorators import role_required
from django.contrib.auth.decorators import login_required
from django.db.models import Sum

# Настройка логгера
logger = logging.getLogger(__name__)


@login_required
@role_required(['student', 'teacher', 'admin'])
def list_test(request):
    user = request.user

    if user.role == 'teacher':
        try:
            teacher = TeacherData.objects.get(data_map=user)
            all_tests = AboutTest.objects.filter(creator=teacher, is_draft=False).order_by('name_tests')
        except TeacherData.DoesNotExist:
            all_tests = []

        tests_for_teacher = [{'test': t, 'is_teacher': True} for t in all_tests]
        return render(request, 'solving_tests/test_selection.html', {
            'tests': tests_for_teacher,
            'is_teacher': True,
            'pusher_key': getattr(settings, 'PUSHER_KEY', ''),
            'pusher_cluster': getattr(settings, 'PUSHER_CLUSTER', 'eu'),
        })

    try:
        student = StudentData.objects.get(data_map=user)
        student_group = student.group
        all_tests = AboutTest.objects.filter(publishedgroup__group_name=student_group).distinct()

        tests_with_status = []
        for test in all_tests:
            attempts = StudentResult.objects.filter(student=user, test=test).count()
            remaining_attempts = test.num_of_attempts - attempts

            # Получаем лучший результат студента
            best_result = StudentResult.objects.filter(student=user, test=test).order_by('-result_points').first()

            test_data = {
                'test': test,
                'remaining_attempts': remaining_attempts,
                'is_completed': attempts >= test.num_of_attempts,
                'attempts_count': attempts,
                'best_result': best_result
            }
            tests_with_status.append(test_data)

    except StudentData.DoesNotExist:
        tests_with_status = []

    return render(request, 'solving_tests/test_selection.html', {
        'tests': tests_with_status,
        'pusher_key': getattr(settings, 'PUSHER_KEY', ''),
        'pusher_cluster': getattr(settings, 'PUSHER_CLUSTER', 'eu'),
    })


def get_randomized_test_for_student(test, student_id, attempt_number=1):
    """
    Генерирует рандомизированный вариант теста для студента
    На основе student_id, test_id и attempt_number создается seed для генератора случайных чисел
    чтобы каждая попытка давала уникальный вариант

    Логика рандомизации:
    - Если тест использует новую систему TaskGroup, то из каждой группы выбираем случайный вариант
    - Если тест использует старую систему, группируем задания по block_expression_num
    - Из каждого блока/группы выбираем случайное задание для студента
    - Сортируем по номеру для правильного порядка отображения
    - Каждая попытка генерирует новый вариант
    """
    # Создаем seed на основе id студента, id теста и номера попытки
    seed = hash(f"{student_id}_{test.id}_{attempt_number}") % (2**32)
    random.seed(seed)

    randomized_expressions = []

    # Проверяем, использует ли тест новую систему TaskGroup
    task_groups = test.task_groups.all()

    if task_groups.exists():
        # Новая система: используем TaskGroup и TaskVariant
        from create_tests.models import TypeNormForTaskVariant

        for task_group in task_groups.order_by('number', 'id'):
            variants = task_group.variants.order_by('id')
            if variants:
                # Выбираем случайный вариант из группы
                selected_variant = random.choice(list(variants))

                # Получаем норму матрицы для TaskVariant
                norm_for_task = TypeNormForTaskVariant.objects.filter(task_variant=selected_variant).first()

                randomized_expressions.append({
                    'user_expression': selected_variant.user_expression,
                    'user_ans': selected_variant.user_ans,
                    'true_ans': selected_variant.true_ans,
                    'user_eps': selected_variant.user_eps,
                    'user_type': selected_variant.user_type,
                    'points_for_solve': task_group.points_for_solve,
                    'exist_select': selected_variant.exist_select,
                    'matrix_norm': norm_for_task.matrix_norms if norm_for_task else None,
                    'number': task_group.number,
                    'block_expression_num': task_group.number
                })
    else:
        # Старая система: используем AboutExpressions
        from collections import defaultdict
        blocks = defaultdict(list)

        for ex in test.expressions.order_by('block_expression_num', 'id'):
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
@role_required(['student', 'teacher', 'admin'])
def some_test_for_student(request, slug_name):
    test = get_object_or_404(AboutTest, name_slug_tests=slug_name)
    student = request.user
    is_teacher = student.role == 'teacher'

    if not is_teacher:
        attempt_count = StudentResult.objects.filter(student=student, test=test).count()
        if attempt_count >= test.num_of_attempts:
            return redirect('solving_tests:view_completed_result', slug_name=slug_name)
    else:
        attempt_count = 0

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
                # Multiple choice question - проверяем правильность выбранных вариантов
                # Разбираем варианты ответов и правильные ответы
                available_options = expr_data['user_ans'].split(';') if expr_data['user_ans'] else []
                correct_answers = expr_data['true_ans'].split(';') if expr_data['true_ans'] else []

                # Получаем выбранные пользователем варианты
                if isinstance(user_ans, str):
                    selected_options = user_ans.split(';') if user_ans else []
                elif isinstance(user_ans, list):
                    selected_options = user_ans
                else:
                    selected_options = []

                # Проверяем правильность: каждый выбранный вариант должен быть правильным,
                # и не должно быть пропущенных правильных вариантов
                res = 1  # Начинаем с полного балла

                # Создаем множества для сравнения
                selected_set = set(selected_options)

                # Определяем какие варианты должны быть выбраны (где true_ans[j] == '1')
                should_be_selected = set()
                for j, is_correct in enumerate(correct_answers):
                    if j < len(available_options) and is_correct == '1':
                        should_be_selected.add(available_options[j])

                # Проверяем точное совпадение
                if selected_set != should_be_selected:
                    res = 0

                logger.info(f"Question {i+1}: Multiple choice - Selected: {selected_set}, Should be: {should_be_selected}, Result: {res}")
            else:
                # Single answer question
                if expr_data['user_type'] and expr_data['user_type'].type_code == 5:
                    # Свободный ответ — проверяется преподавателем вручную
                    res = 0
                elif expr_data['user_type'].type_code == 4:  # Matrix type
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

        # Используем критерии оценивания из настроек теста
        if score_in_pr >= test.grade_5_threshold:
            grade = 5
        elif score_in_pr >= test.grade_4_threshold:
            grade = 4
        elif score_in_pr >= test.grade_3_threshold:
            grade = 3
        else:
            grade = 2

        # Если есть вопросы со свободным ответом — оценка не выставляется пока препод не проверит
        has_free_answers = any(
            expr_data.get('user_type') and expr_data['user_type'].type_code == 5
            for expr_data in expressions_data
        )

        request.session['test_result'] = {
            'result': result_score,
            'score': grade,
            'test_name': test.name_tests,
            'is_teacher': is_teacher,
            'has_free_answers': has_free_answers,
        }

        if is_teacher:
            # Для преподавателя сохраняем детальные результаты в сессии, не пишем в БД
            detailed_results = []
            for i, expr_data in enumerate(expressions_data):
                student_answer = student_answers[i] if i < len(student_answers) else ''
                if expr_data['exist_select']:
                    available_options = expr_data['user_ans'].split(';') if expr_data['user_ans'] else []
                    correct_answers_flags = expr_data['true_ans'].split(';') if expr_data['true_ans'] else []
                    correct_options = [
                        available_options[j]
                        for j, flag in enumerate(correct_answers_flags)
                        if j < len(available_options) and flag == '1'
                    ]
                    detailed_results.append({
                        'question_number': i + 1,
                        'question': expr_data['user_expression'],
                        'student_answer': student_answer,
                        'correct_answer': '; '.join(correct_options),
                        'is_multiple_choice': True,
                        'options': available_options,
                        'points': expr_data['points_for_solve'],
                    })
                else:
                    is_free = expr_data['user_type'] and expr_data['user_type'].type_code == 5
                    detailed_results.append({
                        'question_number': i + 1,
                        'question': expr_data['user_expression'],
                        'student_answer': student_answer,
                        'correct_answer': None if is_free else expr_data['user_ans'],
                        'is_multiple_choice': False,
                        'is_free_answer': is_free,
                        'options': [],
                        'points': expr_data['points_for_solve'],
                    })
            request.session['teacher_detailed_results'] = {
                'detailed_results': detailed_results,
                'count': all_points,
            }
        else:
            StudentResult.objects.create(
                student=student,
                test=test,
                attempt_number=attempt_count + 1,
                result_points=result_score,
                max_points=all_points,
                res_answer=json.dumps(student_answers),
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
@role_required(['student', 'teacher', 'admin'])
def show_result(request, slug_name):
    test_result = request.session.get('test_result')

    if not test_result:
        return redirect('list_test')

    test = AboutTest.objects.get(name_slug_tests=slug_name)
    student = request.user
    is_teacher = test_result.get('is_teacher', False)

    if is_teacher:
        # Для преподавателя берём данные из сессии, всегда показываем детальные результаты
        teacher_data = request.session.get('teacher_detailed_results', {})
        context = {
            'test_name': test_result['test_name'],
            'result': test_result['result'],
            'score': test_result['score'],
            'count': teacher_data.get('count', 0),
            'slug_name': slug_name,
            'result_display_mode': 'show_correct',
            'detailed_results': teacher_data.get('detailed_results', []),
            'show_correct_answers': True,
            'is_teacher': True,
        }
        return render(request, 'solving_tests/result.html', context)

    # Получаем максимальные баллы из сохранённого результата
    latest_result = StudentResult.objects.filter(student=student, test=test).order_by('-attempt_number').first()

    if latest_result:
        count = latest_result.max_points
    else:
        count = 0

    # Получаем настройки отображения результатов
    result_display_mode = getattr(test, 'result_display_mode', 'only_score')

    # Если тест содержит свободные ответы — показываем сообщение об ожидании проверки
    has_free_answers = test_result.get('has_free_answers', False)
    waiting_for_review = has_free_answers  # студент ждёт пока препод не проверит

    # Базовый контекст
    context = {
        'test_name': test_result['test_name'],
        'result': test_result['result'],
        'score': test_result['score'],
        'count': count,
        'slug_name': slug_name,
        'result_display_mode': result_display_mode,
        'waiting_for_review': waiting_for_review,
    }

    # Добавляем дополнительную информацию в зависимости от режима отображения
    if result_display_mode == 'show_correct':
        # Показываем правильные ответы - получаем детальные результаты
        student = request.user

        # Получаем последний результат студента для этого теста
        latest_result = StudentResult.objects.filter(student=student, test=test).order_by('-attempt_number').first()

        if latest_result:
            # Получаем рандомизированный вариант теста, который проходил студент
            expressions_data = get_randomized_test_for_student(test, student.id, latest_result.attempt_number)

            # Получаем ответы студента
            try:
                student_answers = json.loads(latest_result.res_answer)
            except (json.JSONDecodeError, ValueError):
                # Пытаемся обработать старый формат (строковое представление Python списка)
                try:
                    # Используем ast.literal_eval для безопасной оценки строкового представления Python
                    import ast
                    student_answers = ast.literal_eval(latest_result.res_answer)
                except (ValueError, SyntaxError):
                    student_answers = []

            # Подготавливаем детальную информацию для каждого вопроса
            detailed_results = []
            for i, expr_data in enumerate(expressions_data):
                student_answer = student_answers[i] if i < len(student_answers) else ''

                # Получаем правильные ответы
                if expr_data['exist_select']:
                    # Для вопросов с множественным выбором
                    available_options = expr_data['user_ans'].split(';') if expr_data['user_ans'] else []
                    correct_answers = expr_data['true_ans'].split(';') if expr_data['true_ans'] else []

                    correct_options = []
                    for j, flag in enumerate(correct_answers):
                        if j < len(available_options) and flag == '1':
                            correct_options.append(available_options[j])

                    if isinstance(student_answer, str):
                        selected_options = student_answer.split(';') if student_answer else []
                    elif isinstance(student_answer, list):
                        selected_options = student_answer
                    else:
                        selected_options = []
                    is_correct = set(selected_options) == set(correct_options)

                    detailed_results.append({
                        'question_number': i + 1,
                        'question': expr_data['user_expression'],
                        'student_answer': student_answer,
                        'correct_answer': '; '.join(correct_options),
                        'is_multiple_choice': True,
                        'options': available_options,
                        'points': expr_data['points_for_solve'],
                        'is_correct': is_correct,
                    })
                else:
                    # Для обычных вопросов
                    try:
                        if expr_data['user_type'].type_code == 4 and expr_data.get('matrix_norm'):
                            res = CheckAnswer(expr_data['user_ans'], student_answer, False,
                                            expression=expr_data['user_expression'],
                                            type_ans=expr_data['user_type'].type_code,
                                            type_norm=expr_data['matrix_norm']).compare_answer()
                        else:
                            res = CheckAnswer(expr_data['user_ans'], student_answer, False,
                                            expression=expr_data['user_expression'],
                                            type_ans=expr_data['user_type'].type_code).compare_answer()
                        is_correct = res == 1
                    except Exception:
                        is_correct = None
                    detailed_results.append({
                        'question_number': i + 1,
                        'question': expr_data['user_expression'],
                        'student_answer': student_answer,
                        'correct_answer': expr_data['user_ans'],
                        'is_multiple_choice': False,
                        'options': [],
                        'points': expr_data['points_for_solve'],
                        'is_correct': is_correct,
                    })

            context['detailed_results'] = detailed_results
            context['show_correct_answers'] = True
        else:
            context['show_correct_answers'] = False
    else:  # only_score
        # Показываем только баллы
        context['show_correct_answers'] = False
        context['show_student_answers'] = False

    return render(request, 'solving_tests/result.html', context)


@login_required
@role_required(['student', 'teacher', 'admin'])
def view_completed_result(request, slug_name):
    """Просмотр результатов пройденного теста"""
    test = get_object_or_404(AboutTest, name_slug_tests=slug_name)
    student = request.user

    # Получаем результаты студента для этого теста
    results = StudentResult.objects.filter(student=student, test=test).order_by('-attempt_number')

    if not results.exists():
        return redirect('solving_tests:list_test')

    # Берем лучший результат
    best_result = results.order_by('-result_points').first()

    # Используем сохранённые максимальные баллы
    count = best_result.max_points

    # Получаем настройки отображения результатов
    result_display_mode = getattr(test, 'result_display_mode', 'only_score')

    # Проверяем наличие вопросов со свободным ответом и статус их проверки
    expressions_data = get_randomized_test_for_student(test, student.id, best_result.attempt_number)
    free_q_indices = [
        i for i, e in enumerate(expressions_data)
        if e.get('user_type') and e['user_type'].type_code == 5
    ]
    has_free_answers = bool(free_q_indices)
    if has_free_answers:
        from solving_tests.models import FreeAnswerGrade
        graded_count = FreeAnswerGrade.objects.filter(
            student_result=best_result,
            question_index__in=free_q_indices,
            is_correct__isnull=False,
        ).count()
        waiting_for_review = graded_count < len(free_q_indices)
    else:
        waiting_for_review = False

    score_pct = best_result.result_points / count * 100 if count > 0 else 0
    grade = (5 if score_pct >= test.grade_5_threshold else
             4 if score_pct >= test.grade_4_threshold else
             3 if score_pct >= test.grade_3_threshold else 2)

    # Базовый контекст
    context = {
        'test_name': test.name_tests,
        'test': test,
        'result': best_result.result_points,
        'score': grade,
        'count': count,
        'slug_name': slug_name,
        'result_display_mode': result_display_mode,
        'best_result': best_result,
        'all_results': results,
        'waiting_for_review': waiting_for_review,
        'has_free_answers': has_free_answers,
    }

    # Добавляем дополнительную информацию в зависимости от режима отображения
    if result_display_mode == 'show_correct':

        # Получаем ответы студента
        try:
            student_answers = json.loads(best_result.res_answer)
        except (json.JSONDecodeError, ValueError):
            try:
                import ast
                student_answers = ast.literal_eval(best_result.res_answer)
            except (ValueError, SyntaxError):
                student_answers = []

        # Подготавливаем детальную информацию для каждого вопроса
        detailed_results = []
        for i, expr_data in enumerate(expressions_data):
            student_answer = student_answers[i] if i < len(student_answers) else ''

            if expr_data['exist_select']:
                available_options = expr_data['user_ans'].split(';') if expr_data['user_ans'] else []
                correct_answers = expr_data['true_ans'].split(';') if expr_data['true_ans'] else []

                correct_options = []
                for j, flag in enumerate(correct_answers):
                    if j < len(available_options) and flag == '1':
                        correct_options.append(available_options[j])

                if isinstance(student_answer, str):
                    selected_options = student_answer.split(';') if student_answer else []
                elif isinstance(student_answer, list):
                    selected_options = student_answer
                else:
                    selected_options = []
                is_correct = set(selected_options) == set(correct_options)

                detailed_results.append({
                    'question_number': i + 1,
                    'question': expr_data['user_expression'],
                    'student_answer': student_answer,
                    'correct_answer': '; '.join(correct_options),
                    'is_multiple_choice': True,
                    'options': available_options,
                    'points': expr_data['points_for_solve'],
                    'is_correct': is_correct,
                })
            else:
                try:
                    if expr_data['user_type'].type_code == 4 and expr_data.get('matrix_norm'):
                        res = CheckAnswer(expr_data['user_ans'], student_answer, False,
                                        expression=expr_data['user_expression'],
                                        type_ans=expr_data['user_type'].type_code,
                                        type_norm=expr_data['matrix_norm']).compare_answer()
                    else:
                        res = CheckAnswer(expr_data['user_ans'], student_answer, False,
                                        expression=expr_data['user_expression'],
                                        type_ans=expr_data['user_type'].type_code).compare_answer()
                    is_correct = res == 1
                except Exception:
                    is_correct = None
                detailed_results.append({
                    'question_number': i + 1,
                    'question': expr_data['user_expression'],
                    'student_answer': student_answer,
                    'correct_answer': expr_data['user_ans'],
                    'is_multiple_choice': False,
                    'options': [],
                    'points': expr_data['points_for_solve'],
                    'is_correct': is_correct,
                })

        context['detailed_results'] = detailed_results
        context['show_correct_answers'] = True
    else:
        context['show_correct_answers'] = False
        context['show_student_answers'] = False

    return render(request, 'solving_tests/result.html', context)
