import uuid

from django.contrib.auth import logout
from django.core.checks import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.text import slugify
from unidecode import unidecode

from .models import AboutExpressions, AboutTest, Subjects, PublishedGroup, TypeAnswer
from users.models import StudentGroup, StudentInstitute, TeacherData
import json
from django.http import JsonResponse
from .decorators import role_required
from django.contrib.auth.decorators import login_required
from datetime import timedelta
import logging
from django.views.decorators.csrf import csrf_exempt
import datetime


logger = logging.getLogger(__name__)

def parse_duration_string(time_str):
    try:
        parts = time_str.split(':')
        if len(parts) != 3:
            raise ValueError("Неверный формат времени. Ожидается HH:MM:SS.")

        hours, minutes, seconds = map(int, parts)
        if not (0 <= minutes < 60) or not (0 <= seconds < 60) or hours < 0:
            raise ValueError("Неверное значение времени.")

        return timedelta(hours=hours, minutes=minutes, seconds=seconds)

    except Exception as e:
        raise ValueError(f"Ошибка обработки времени: {e}")


@login_required
@role_required(['teacher', 'admin'])
def create_test(request):
    all_subj = Subjects.objects.all()
    all_types_answer = TypeAnswer.objects.all()

    if request.method == 'POST':
        try:
            test_name = request.POST.get('name_test')
            time_to_sol_raw = request.POST.get('time_solve')
            count_attempts = request.POST.get('num_attempts')
            description_test = request.POST.get('description_test', '')
            subj_id = request.POST.get('subj_test')
            subj = Subjects.objects.get(id=subj_id)
            time_to_sol = parse_duration_string(time_to_sol_raw)

            # Получение списков из формы
            points = json.loads(request.POST.get('point_solve', '[]'))
            expressions = json.loads(request.POST.get('user_expression', '[]'))
            answers = json.loads(request.POST.get('user_ans', '[]'))
            boolAns = json.loads(request.POST.get('user_bool_ans', '[]'))
            epsilons = json.loads(request.POST.get('user_eps', '[]'))
            types = json.loads(request.POST.get('user_type', '[]'))

            # Сохраняем тест
            test_slug = slugify(unidecode(test_name))
            new_test = AboutTest.objects.create(
                name_tests=test_name,
                time_to_solution=time_to_sol,
                name_slug_tests=test_slug,
                num_of_attempts=count_attempts,
                subj=subj,
                description=description_test,
                is_draft=False
            )

            # Добавляем задания
            for expr, ans, t_ans, eps, type_id, point, bool_ans in zip(expressions, answers, boolAns, epsilons, types, points, boolAns):
                flag_select = ';' in bool_ans
                type_obj = TypeAnswer.objects.get(id=type_id)

                expr_instance = AboutExpressions.objects.create(
                    user_expression=expr,
                    user_ans=ans,
                    true_ans=t_ans,
                    user_eps=eps,
                    user_type=type_obj,
                    points_for_solve=point,
                    exist_select=flag_select
                )
                new_test.expressions.add(expr_instance)

            new_test.save()
            return redirect('create_tests:test_list')

        except Exception as e:
            return render(request, 'create_tests/writing_tests.html', {
                'all_subj': all_subj,
                'all_types_answer': all_types_answer,
                'error_msg': str(e)
            })

    return render(request, 'create_tests/writing_tests.html',
                  {'all_subj': all_subj,
                   'all_types_answer': all_types_answer})


@login_required
@role_required(['teacher', 'admin'])
def test_list(request):
    all_groups = StudentGroup.objects.all().select_related('institute')
    institutes = StudentInstitute.objects.all().prefetch_related('studentgroup_set')

    # Получаем опубликованные тесты и черновики отдельно
    tests = AboutTest.objects.filter(is_draft=False)
    drafts = AboutTest.objects.filter(is_draft=True)

    published = PublishedGroup.objects.select_related('group_name', 'test_name')
    published_groups = [pg.group_name for pg in published]

    return render(request, 'create_tests/all_test_for_teach.html', {
        'tests': tests,
        'drafts': drafts,
        'all_groups': all_groups,
        'institutes': institutes,
        'groups': published_groups,
        'published': published
    })



@login_required
@role_required(['teacher', 'admin'])
def some_test(request, slug_name):
    test = get_object_or_404(AboutTest, name_slug_tests=slug_name)
    expressions = test.expressions.all()
    numbered_expressions = [
        {"number": idx + 1, "expression": ex} for idx, ex in enumerate(expressions)
    ]
    return render(request, 'create_tests/some_test.html', {
        'test': test,
        'numbered_expressions': numbered_expressions
    })


@login_required
@role_required(['teacher', 'admin'])
def delete_test(request, slug_name):
    if request.method == "POST":
        try:
            test = get_object_or_404(AboutTest, name_slug_tests=slug_name)
            test.delete()
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)
    return JsonResponse({"error": "Неверный метод запроса"}, status=405)


@login_required
@role_required(['teacher', 'admin'])
def publish_test(request, slug_name):
    if request.method == "POST":
        try:
            test = get_object_or_404(AboutTest, name_slug_tests=slug_name)
            teacher = get_object_or_404(TeacherData, data_map=request.user)
            data = json.loads(request.body)
            group_ids = data.get('groups', [])

            # Удаляем предыдущие публикации
            PublishedGroup.objects.filter(test_name=test).delete()

            # Создаем новые записи публикации
            for group_id in group_ids:
                group = get_object_or_404(StudentGroup, id=group_id)
                PublishedGroup.objects.create(
                    test_name=test,
                    teacher_name=teacher,
                    group_name=group
                )

            test.is_published = 1
            test.save()
            return JsonResponse({'success': True})

        except Exception as e:
            logger.error(f"Publish error: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)


@login_required
@role_required(['teacher', 'admin'])
def unpublish_test(request, slug_name):
    if request.method == "POST":
        try:
            test = AboutTest.objects.get(name_slug_tests=slug_name)
            PublishedGroup.objects.filter(test_name=test).delete()
            test.is_published = False
            test.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)


@login_required
@role_required(['teacher', 'admin'])
@csrf_exempt
def save_draft(request):
    """Сохранение черновика теста"""
    if request.method == 'POST':
        try:
            # Получаем данные из запроса
            test_name = request.POST.get('name_test', 'Черновик')
            time_to_sol_raw = request.POST.get('time_solve', '01:00:00')
            count_attempts = request.POST.get('num_attempts', '1')
            description_test = request.POST.get('description_test', '')
            subj_id = request.POST.get('subj_test')

            # Парсим время
            try:
                time_to_sol = parse_duration_string(time_to_sol_raw)
            except:
                time_to_sol = timedelta(hours=1)

            # Получаем предмет или используем по умолчанию
            if subj_id:
                subj = Subjects.objects.get(id=subj_id)
            else:
                subj = Subjects.objects.first()

            # Получение списков из формы
            points = json.loads(request.POST.get('point_solve', '[]'))
            expressions = json.loads(request.POST.get('user_expression', '[]'))
            answers = json.loads(request.POST.get('user_ans', '[]'))
            boolAns = json.loads(request.POST.get('user_bool_ans', '[]'))
            epsilons = json.loads(request.POST.get('user_eps', '[]'))
            types = json.loads(request.POST.get('user_type', '[]'))

            # Создаем уникальный slug для черновика
            base_slug = slugify(unidecode(test_name))
            unique_slug = f"{base_slug}-draft-{uuid.uuid4().hex[:8]}"

            # Сохраняем черновик
            draft_test = AboutTest.objects.create(
                name_tests=test_name,
                time_to_solution=time_to_sol,
                name_slug_tests=unique_slug,
                num_of_attempts=int(count_attempts) if count_attempts else 1,
                subj=subj,
                description=description_test,
                is_draft=True
            )

            # Добавляем задания если они есть
            if expressions and len(expressions) > 0:
                for i, expr in enumerate(expressions):
                    if expr.strip():  # Проверяем что выражение не пустое
                        ans = answers[i] if i < len(answers) else ''
                        bool_ans = boolAns[i] if i < len(boolAns) else '1'
                        eps = epsilons[i] if i < len(epsilons) else '0'
                        type_id = types[i] if i < len(types) else None
                        point = points[i] if i < len(points) else 1

                        flag_select = ';' in bool_ans
                        type_obj = None
                        if type_id:
                            try:
                                type_obj = TypeAnswer.objects.get(id=type_id)
                            except:
                                type_obj = TypeAnswer.objects.first()

                        expr_instance = AboutExpressions.objects.create(
                            user_expression=expr,
                            user_ans=ans,
                            true_ans=bool_ans,
                            user_eps=eps,
                            user_type=type_obj,
                            points_for_solve=int(point) if point else 1,
                            exist_select=flag_select
                        )
                        draft_test.expressions.add(expr_instance)

            draft_test.save()
            return JsonResponse({
                'success': True,
                'message': 'Черновик сохранен',
                'draft_id': draft_test.id,
                'redirect_url': '/create_tests/listTests/'
            })

        except Exception as e:
            logger.error(f"Error saving draft: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'Ошибка при сохранении черновика: {str(e)}'
            }, status=400)

    return JsonResponse({'success': False, 'error': 'Неверный метод запроса'}, status=405)


@login_required
@role_required(['teacher', 'admin'])
def continue_draft(request, slug_name):
    """Продолжить работу с черновиком"""
    return redirect('create_tests:edit_test', slug_name=slug_name)


@login_required
@role_required(['teacher', 'admin'])
def create_draft_test(request):
    # Создаем пустой черновик и редиректим на редактирование
    draft_test = AboutTest.objects.create(
        name_tests='Новый черновик',
        num_of_attempts=1,
        description='',
        time_to_solution=timedelta(minutes=30),
        is_draft=True,
        user=request.user  # если есть привязка к автору
    )
    return redirect('create_tests:edit_test', slug_name=draft_test.name_slug_tests)


@login_required
@role_required(['teacher', 'admin'])
def edit_test(request, slug_name):
    test = get_object_or_404(AboutTest, name_slug_tests=slug_name)
    all_subj = Subjects.objects.all()
    all_types_answer = TypeAnswer.objects.all()

    if request.method == 'POST':
        try:
            # Определяем, публикуем ли мы черновик или сохраняем как черновик
            action = request.POST.get('action', 'save')

            # Обновляем основные поля теста
            test.name_tests = request.POST.get('name_test', test.name_tests)
            test.num_of_attempts = int(request.POST.get('num_attempts', test.num_of_attempts))
            test.description = request.POST.get('description_test', test.description)

            # Обновляем предмет
            subj_id = request.POST.get('subj_test')
            if subj_id:
                test.subj = Subjects.objects.get(id=subj_id)

            # Обновляем время (парсим из строки формата HH:MM:SS)
            time_to_sol_raw = request.POST.get('time_solve')
            test.time_to_solution = parse_duration_string(time_to_sol_raw)

            # Получение списков из формы (как в create_test)
            points = json.loads(request.POST.get('point_solve', '[]'))
            expressions = json.loads(request.POST.get('user_expression', '[]'))
            answers = json.loads(request.POST.get('user_ans', '[]'))
            boolAns = json.loads(request.POST.get('user_bool_ans', '[]'))
            epsilons = json.loads(request.POST.get('user_eps', '[]'))
            types = json.loads(request.POST.get('user_type', '[]'))

            # Удаляем старые выражения
            test.expressions.all().delete()

            # Добавляем новые выражения
            for expr, ans, bool_ans, eps, type_id, point in zip(expressions, answers, boolAns, epsilons, types, points):
                if expr.strip():  # Проверяем что выражение не пустое
                    flag_select = ';' in bool_ans
                    type_obj = TypeAnswer.objects.get(id=type_id) if type_id else None

                    expr_instance = AboutExpressions.objects.create(
                        user_expression=expr,
                        user_ans=ans,
                        true_ans=bool_ans,
                        user_eps=eps,
                        user_type=type_obj,
                        points_for_solve=int(point) if point else 1,
                        exist_select=flag_select
                    )
                    test.expressions.add(expr_instance)

            # Определяем статус теста в зависимости от действия
            if action == 'publish':
                test.is_draft = False
                # Обновляем slug если это был черновик
                if 'draft' in test.name_slug_tests:
                    test.name_slug_tests = slugify(unidecode(test.name_tests))
            elif action == 'save_draft':
                test.is_draft = True

            test.save()
            messages.success(request, 'Тест успешно сохранен!')
            return redirect('create_tests:test_list')

        except Exception as e:
            messages.error(request, f"Ошибка при сохранении: {str(e)}")
            return redirect('create_tests:edit_test', slug_name=slug_name)

    # GET запрос - подготовка данных для отображения
    expressions_data = []
    for expr in test.expressions.all():
        # Разбираем данные выражения для отображения
        ans_list = expr.user_ans.split(';') if ';' in expr.user_ans else [expr.user_ans]
        eps_list = expr.user_eps.split(';') if ';' in expr.user_eps else [expr.user_eps]
        bool_list = expr.true_ans.split(';') if ';' in expr.true_ans else [expr.true_ans]

        # Подготавливаем список ответов
        answers_data = []
        for i, (ans, eps, bool_val) in enumerate(zip(ans_list, eps_list, bool_list)):
            answers_data.append({
                'user_ans': ans,
                'user_eps': eps,
                'user_type_id': expr.user_type.id if expr.user_type else '',
                'is_correct': bool_val == '1'
            })

        expressions_data.append({
            'user_expression': expr.user_expression,
            'points_for_solve': expr.points_for_solve,
            'answers': answers_data
        })

    # Разбираем время для отображения
    total_seconds = int(test.time_to_solution.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    context = {
        'test': test,
        'expressions_data': expressions_data,
        'all_subj': all_subj,
        'all_types_answer': all_types_answer,
        'hours': hours,
        'minutes': minutes,
        'seconds': seconds,
        'is_editing': True,
    }
    return render(request, 'create_tests/writing_tests.html', context)
