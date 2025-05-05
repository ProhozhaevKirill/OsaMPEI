from django.shortcuts import render, redirect, get_object_or_404
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from .models import AboutExpressions, AboutTest, Subjects
from users.models import StudentGroup, StudentInstitute
import json
from django.http import JsonResponse
from .decorators import role_required
from django.contrib.auth.decorators import login_required
from datetime import timedelta


def parse_duration_string(time_str):
    try:
        h, m, s = map(int, time_str.split(':'))
        return timedelta(hours=h, minutes=m, seconds=s)
    except:
        return timedelta(hours=1, minutes=30)  # fallback


@login_required
@role_required(['teacher', 'admin'])
def create_test(request):
    all_subj = Subjects.objects.all()

    if request.method == 'POST':
        test_name = request.POST.get('name_test')
        time_to_sol_raw = request.POST.get('time_solve')
        time_to_sol = parse_duration_string(time_to_sol_raw)
        subj_id = request.POST.get('subj_test')
        subj = Subjects.objects.get(id=subj_id)
        description_test = request.POST.get('description_test')

        points = json.loads(request.POST.get('point_solve', '[]'))
        expressions = json.loads(request.POST.get('user_expression', '[]'))
        answers = json.loads(request.POST.get('user_ans', '[]'))
        boolAns = json.loads(request.POST.get('user_bool_ans', '[]'))
        epsilons = json.loads(request.POST.get('user_eps', '[]'))

        # Создание теста
        test_slug = slugify(test_name)
        new_test = AboutTest.objects.create(
            name_tests=test_name,
            time_to_solution=time_to_sol,
            name_slug_tests=test_slug,
            subj=subj,
            description=description_test,
        )

        # Создание выражений и добавление их в тест
        for expr, ans, t_ans, eps, point, bool_ans in zip(expressions, answers, boolAns, epsilons, points, boolAns):
            # Определяем, есть ли варианты ответа

            # Переписать точки с запятой, убрав их, дабы потом двоичный в десятичный и сравнивать инты в проверке
            # Определять есть ли выбор по наличию чекбоксов мб или типо того, пока припроверке костыль с удалением точек с запятой
            flag_select = True if ';' in bool_ans else False

            expression_instance = AboutExpressions.objects.create(
                user_expression=expr,
                user_ans=ans,
                true_ans=t_ans,
                user_eps=eps,
                points_for_solve=point,
                exist_select=flag_select
            )
            new_test.expressions.add(expression_instance)

        new_test.save()

        # Редирект на страницу списка тестов после сохранения
        return redirect('test_list')

    return render(request, 'create_tests/writing_tests.html', {'all_subj': all_subj})


@login_required
@role_required(['teacher', 'admin'])
def test_list(request):
    # Получаем ВСЕ группы и институты, а не одну случайную
    groups = StudentGroup.objects.all().select_related('institute')
    institutes = StudentInstitute.objects.all().prefetch_related('studentgroup_set')

    tests = AboutTest.objects.all()

    return render(request, 'create_tests/all_test_for_teach.html',
                  {
                      'tests': tests,
                      'groups': groups,
                      'institutes': institutes
                  })


@login_required
@role_required(['teacher', 'admin'])
def some_test(request, slug_name):
    test = AboutTest.objects.get(name_slug_tests=slug_name)
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
def delete_test(request, slug):
    if request.method == "POST":
        test = get_object_or_404(AboutTest, name_slug_tests=slug)
        test.expressions.all().delete()
        test.delete()
        return JsonResponse({"success": True})
    return JsonResponse({"error": "Неверный метод запроса"}, status=400)


# @require_POST
# @role_required(['teacher', 'admin'])
# def publish_test(request, test_id):
#     try:
#         test = AboutTest.objects.get(pk=test_id)
#         group_ids = request.POST.getlist('groups')
#
#         # Очищаем текущие группы и добавляем новые
#         test.allowed_groups.clear()
#         groups = StudentGroup.objects.filter(id__in=group_ids)
#         test.allowed_groups.add(*groups)
#
#         test.is_published = True
#         test.save()
#
#         return JsonResponse({'status': 'success'})
#     except Exception as e:
#         return JsonResponse({'status': 'error', 'message': str(e)})