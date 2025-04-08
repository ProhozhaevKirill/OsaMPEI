from django.shortcuts import render, get_object_or_404, redirect
from create_tests.models import AboutExpressions, AboutTest
from .models import StudentResult
from logic_of_expression.check_sympy_expr import CheckAnswer
import numpy as np
import json


def list_test(request):
    tests = AboutTest.objects.all()
    return render(request, 'solving_tests/test_selection.html', {'tests': tests})

def some_test_for_student(request, slug_name):
    test = get_object_or_404(AboutTest, name_slug_tests=slug_name)

    if request.method == 'POST':
        binary_answers = request.POST.get('binary_answers', '')
        student_answers = binary_answers.split(';')

        right_answers = [ex.user_ans for ex in test.expressions.all()]
        is_choice = [ex.exist_select for ex in test.expressions.all()]
        var_true_ans = [ex.true_ans for ex in test.expressions.all()]
        points = [ex.points_for_solve for ex in test.expressions.all()]
        all_p = np.sum(points)

        result_score = 0
        for i in range(len(right_answers)):
            if is_choice[i]:
                var_true_ans[i] = var_true_ans[i].replace(';', '')
                res = CheckAnswer(var_true_ans[i], student_answers[i], is_choice[i]).compare_answer()
            else:
                res = CheckAnswer(right_answers[i], student_answers[i], is_choice[i]).compare_answer()
            result_score += res * points[i]

        # Вычисляем процент и оценку
        score_in_pr = result_score / all_p * 100
        if score_in_pr >= 80:
            score = 5
        elif 60 <= score_in_pr < 80:
            score = 4
        elif 35 <= score_in_pr < 60:
            score = 3
        else:
            score = 2

        # Сохраняем результаты в сессии
        request.session['test_result'] = {
            'result': result_score,
            'score': score,
            'test_name': test.name_tests,
        }

        # Редирект на страницу с результатами
        return redirect('show_result', slug_name=slug_name)

    # Если запрос GET, отображаем тест
    expressions = test.expressions.all()

    # Формируем список выражений с вариантами ответа
    expressions_with_options = []
    for ex in expressions:
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



def show_result(request, slug_name):
    test_result = request.session.get('test_result', None)

    if not test_result:
        return redirect('list_test')

    return render(request, 'solving_tests/result.html', {
        'test_name': test_result['test_name'],
        'result': test_result['result'],
        'score': test_result['score'],
        'slug_name': slug_name,
    })


#
# from django.http import HttpResponse
# from django.shortcuts import render, get_object_or_404, redirect
# from create_tests.models import AboutExpressions, AboutTest
# from .models import StudentResult  # Модель для хранения результатов теста
# import json
#
#
# def list_test(request):
#     tests = AboutTest.objects.all()
#     return render(request, 'solving_tests/test_selection.html', {'tests': tests})
#
#
# def some_test_for_student(request, slug_name):
#     test = get_object_or_404(AboutTest, name_slug_tests=slug_name)
#
#     if request.method == 'POST':
#         # Получаем строку с ответами, отправленными через скрытое поле
#         binary_answers = request.POST.get('binary_answers', '')
#
#         # Преобразуем строку в список (если ответы разделены точкой с запятой)
#         answers = binary_answers.split(';')
#
#         # Сохранение ответов в базу данных
#         for answer in answers:
#             # Создаем объект результата для студента
#             StudentResult.objects.create(test=test, answer_text=answer)
#
#         # Перенаправляем на страницу с результатами
#         return redirect('test_completed')  # Можно перенаправить на страницу с результатами или завершением теста
#
#     # Если это GET-запрос, отображаем форму
#     expressions = test.expressions.all()
#     expressions_with_options = []
#
#     # Собираем все выражения с их возможными вариантами
#     for ex in expressions:
#         options = ex.user_ans.split(';') if ex.user_ans else []
#         expressions_with_options.append({
#             'expression': ex,
#             'options': options,
#             'exist_select': ex.exist_select,
#         })
#
#     return render(request, 'solving_tests/specific_test.html', {
#         'test': test,
#         'expressions_with_options': expressions_with_options,
#     })
