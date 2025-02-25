import json
from django.shortcuts import render, redirect
from django.utils.text import slugify
from .models import AboutExpressions, AboutTest
from django.shortcuts import render, get_object_or_404


def start_page(request):
    return render(request, 'create_tests/navigate.html')


def create_test(request):
    if request.method == 'POST':
        test_name = request.POST.get('name_test')
        time_to_sol = request.POST.get('time_solve')

        points = json.loads(request.POST.get('point_solve', '[]'))
        expressions = json.loads(request.POST.get('user_expression', '[]'))
        answers = json.loads(request.POST.get('user_ans', '[]'))
        epsilons = json.loads(request.POST.get('user_eps', '[]'))
        types = json.loads(request.POST.get('user_type', '[]'))

        test_slug = slugify(test_name)
        new_test = AboutTest.objects.create(
            name_tests=test_name,
            time_to_solution=time_to_sol,
            name_slug_tests=test_slug,
        )

        for expr, ans, eps, typ, point in zip(expressions, answers, epsilons, types, points):
            expression_instance = AboutExpressions.objects.create(
                user_expression=expr,
                user_ans=ans,
                user_eps=eps,
                user_type=typ,
                points_for_solve=point
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

    # Пронумеруем задания вручную
    numbered_expressions = [
        {"number": idx + 1, "expression": ex} for idx, ex in enumerate(expressions)
    ]

    return render(request, 'create_tests/some_test.html', {
        'test': test,
        'numbered_expressions': numbered_expressions
    })


def editing_test(request, id_test):
    test = get_object_or_404(AboutTest, id_test=id_test)

    if request.method == 'POST':
        test.name = request.POST.get('name_test', test.name)
        test.save()

        # Пример обработки связанных вопросов
        for question in test.questions.all():
            new_text = request.POST.get(f'question_{question.id}')
            if new_text:
                question.text = new_text
                question.save()

        return redirect('test_list')  # После сохранения возвращаемся к списку тестов

    return render(request, 'create_tests/editing_tests.html', {
        'test': test,
    })
