from django.shortcuts import render, redirect, get_object_or_404
from django.utils.text import slugify
from .models import AboutExpressions, AboutTest
import json
from django.http import JsonResponse


def start_page(request):
    return render(request, 'create_tests/navigate.html')

def create_test(request):
    if request.method == 'POST':
        test_name = request.POST.get('name_test')
        time_to_sol = request.POST.get('time_solve')

        points = json.loads(request.POST.get('point_solve', '[]'))
        expressions = json.loads(request.POST.get('user_expression', '[]'))
        answers = json.loads(request.POST.get('user_ans', '[]'))
        boolAns = json.loads(request.POST.get('user_bool_ans', '[]'))
        epsilons = json.loads(request.POST.get('user_eps', '[]'))
        types = json.loads(request.POST.get('user_type', '[]'))

        # Создание теста
        test_slug = slugify(test_name)
        new_test = AboutTest.objects.create(
            name_tests=test_name,
            time_to_solution=time_to_sol,
            name_slug_tests=test_slug,
        )

        # Создание выражений и добавление их в тест
        for expr, ans, t_ans, eps, typ, point, bool_ans in zip(expressions, answers, boolAns, epsilons, types, points, boolAns):
            # Определяем, есть ли варианты ответа

            # Переписать точки с запятой, убрав их, дабы потом двоичный в десятичный и сравнивать инты в проверке
            # Определять есть ли выбор по наличию чекбоксов мб или типо того, пока припроверке костыль с удалением точек с запятой
            flag_select = True if ';' in bool_ans else False

            expression_instance = AboutExpressions.objects.create(
                user_expression=expr,
                user_ans=ans,
                true_ans=t_ans,
                user_eps=eps,
                user_type=typ,
                points_for_solve=point,
                exist_select=flag_select
            )
            new_test.expressions.add(expression_instance)

        new_test.save()

        # Редирект на страницу списка тестов после сохранения
        return redirect('test_list')

    return render(request, 'create_tests/writing_tests.html')

def test_list(request):
    tests = AboutTest.objects.all()
    return render(request, 'create_tests/all_test_for_teach.html', {'tests': tests})

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

def delete_test(request, slug):
    if request.method == "POST":
        test = get_object_or_404(AboutTest, name_slug_tests=slug)

        # Удаляем связанные выражения
        test.expressions.all().delete()

        # Удаляем сам тест
        test.delete()

        return JsonResponse({"success": True})

    return JsonResponse({"error": "Неверный метод запроса"}, status=400)


