from django.contrib.auth import logout
from django.core.checks import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.text import slugify
from .models import AboutExpressions, AboutTest, Subjects, PublishedGroup
from users.models import StudentGroup, StudentInstitute, TeacherData
import json
from django.http import JsonResponse
from .decorators import role_required
from django.contrib.auth.decorators import login_required
from datetime import timedelta
import logging


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
            test_slug = slugify(test_name, allow_unicode=True)
            new_test = AboutTest.objects.create(
                name_tests=test_name,
                time_to_solution=time_to_sol,
                name_slug_tests=test_slug,
                num_of_attempts=count_attempts,
                subj=subj,
                description=description_test,
            )

            # Добавляем задания
            for expr, ans, t_ans, eps, type, point, bool_ans in zip(expressions, answers, boolAns, epsilons, types, points, boolAns):
                flag_select = ';' in bool_ans

                expr_instance = AboutExpressions.objects.create(
                    user_expression=expr,
                    user_ans=ans,
                    true_ans=t_ans,
                    user_eps=eps,
                    user_type=type,
                    points_for_solve=point,
                    exist_select=flag_select
                )
                new_test.expressions.add(expr_instance)

            new_test.save()
            return redirect('create_tests:test_list')

        except Exception as e:
            return render(request, 'create_tests/writing_tests.html', {
                'all_subj': all_subj,
                'error_msg': str(e)
            })

    return render(request, 'create_tests/writing_tests.html', {'all_subj': all_subj})


@login_required
@role_required(['teacher', 'admin'])
def test_list(request):
    all_groups = StudentGroup.objects.all().select_related('institute')
    institutes = StudentInstitute.objects.all().prefetch_related('studentgroup_set')

    tests = AboutTest.objects.all()

    published = PublishedGroup.objects.select_related('group_name', 'test_name')
    published_groups = [pg.group_name for pg in published]

    return render(request, 'create_tests/all_test_for_teach.html', {
        'tests': tests,
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
def edit_test(request, slug_name):
    test = get_object_or_404(AboutTest, name_slug_tests=slug_name)
    all_subj = Subjects.objects.all()

    if request.method == 'POST':
        try:
            # Обновление основной информации теста
            test.name_tests = request.POST.get('name_test', test.name_tests)
            test.num_of_attempts = int(request.POST.get('num_attempts', test.num_of_attempts))
            test.description = request.POST.get('description_test', test.description)

            # Обновление предмета
            subj_id = request.POST.get('subj_test')
            if subj_id:
                test.subj = Subjects.objects.get(id=subj_id)

            # Обновление времени
            hours = int(request.POST.get('hours', 0))
            minutes = int(request.POST.get('minutes', 0))
            seconds = int(request.POST.get('seconds', 0))
            test.time_to_solution = timedelta(hours=hours, minutes=minutes, seconds=seconds)

            # Получаем данные из JSON
            expressions = json.loads(request.POST.get('expressions_json', '[]'))
            points = json.loads(request.POST.get('points_json', '[]'))
            answers = json.loads(request.POST.get('answers_json', '[]'))
            epsilons = json.loads(request.POST.get('epsilons_json', '[]'))
            types = json.loads(request.POST.get('types_json', '[]'))
            bool_answers = json.loads(request.POST.get('bool_answers_json', '[]'))

            # Удаляем старые выражения
            test.expressions.clear()

            # Добавляем новые выражения
            for expr, point, ans_list, eps_list, type_list, bool_list in zip(
                    expressions, points, answers, epsilons, types, bool_answers):
                # Для каждого задания создаем новый объект AboutExpressions
                expr_obj = AboutExpressions.objects.create(
                    user_expression=expr,
                    points_for_solve=point,
                    user_ans=';'.join(ans_list) if len(ans_list) > 1 else ans_list[0],
                    user_eps=';'.join(eps_list) if len(eps_list) > 1 else eps_list[0],
                    user_type=';'.join(type_list) if len(type_list) > 1 else type_list[0],
                    true_ans=';'.join(map(str, bool_list)) if len(bool_list) > 1 else str(bool_list[0]),
                    exist_select=len(ans_list) > 1
                )
                test.expressions.add(expr_obj)

            test.save()
            return redirect('test_list')  # Или другой редирект

        except Exception as e:
            messages.error(request, f"Ошибка при сохранении: {str(e)}")
            return redirect('edit_test', slug=slug_name)

    # GET запрос - подготовка данных
    expressions = []
    for expr in test.expressions.all():
        # Подготавливаем данные для каждого выражения
        expr_data = {
            'id': expr.id,
            'user_expression': expr.user_expression,
            'points_for_solve': expr.points_for_solve,
            'answers': []
        }

        # Разбираем ответы, если их несколько
        ans_list = expr.user_ans.split(';') if ';' in expr.user_ans else [expr.user_ans]
        eps_list = expr.user_eps.split(';') if ';' in expr.user_eps else [expr.user_eps]
        type_list = expr.user_type.split(';') if ';' in expr.user_type else [expr.user_type]
        bool_list = expr.true_ans.split(';') if ';' in expr.true_ans else [expr.true_ans]

        # Собираем ответы для шаблона
        for ans, eps, type_ans, bool_ans in zip(ans_list, eps_list, type_list, bool_list):
            expr_data['answers'].append({
                'user_ans': ans,
                'user_eps': eps,
                'user_type': type_ans,
                'exist_select': bool_ans == '1'
            })

        expressions.append(expr_data)

    # Время для отображения
    total_seconds = test.time_to_solution.total_seconds()
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)

    context = {
        'test': test,
        'expressions': expressions,
        'all_subj': all_subj,
        'hours': hours,
        'minutes': minutes,
        'seconds': seconds,
    }
    return render(request, 'create_tests/editing_tests.html', context)
