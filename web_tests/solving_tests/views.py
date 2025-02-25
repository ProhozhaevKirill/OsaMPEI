from django.shortcuts import render
from create_tests.models import AboutExpressions, AboutTest
from logic_of_expression.check_sympy_expr import CheckAnswer
import numpy as np
import json


def list_test(request):
    tests = AboutTest.objects.all()
    return render(request, 'solving_tests/test_selection.html', {'tests': tests})


def some_test_for_student(request, slug_name):
    global test; test = AboutTest.objects.get(name_slug_tests=slug_name)
    
    if request.method == 'POST':
        
        student_answers = request.POST.getlist('answer')        
        right_answers = [ex.user_ans for ex in test.expressions.all()]
        points = [ex.points_for_solve for ex in test.expressions.all()]
        all_p = np.sum(points)

        all_res = np.array([])
        for student_answer, right_answer in zip(student_answers, right_answers):
            res = CheckAnswer(right_answer, student_answer).compare_answer()
            all_res = np.append(all_res, res)

        result = 0
        if len(points) == len(all_res):
            for i in range(len(points)):
                result += all_res[i] * points[i]

        score_in_pr = result / all_p * 100
        if score_in_pr >= 80:
            score = 5
        elif 60 <= score_in_pr < 80:
            score = 4
        elif 35 <= score_in_pr < 60:
            score = 3
        else:
            score = 2

        return render(request, 'solving_tests/result.html', {'result': result, 'score': score, 'test': test})
    
    return render(request, 'solving_tests/specific_test.html', {'test': test})


def show_result(request):
    return render(request, 'solving_tests/result.html', {'test': test, 'result': all_res})
