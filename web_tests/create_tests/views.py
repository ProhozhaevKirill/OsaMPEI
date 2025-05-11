from django.shortcuts import render, redirect, get_object_or_404
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from .models import AboutExpressions, AboutTest, Subjects, PublishedGroup
from users.models import StudentGroup, StudentInstitute, TeacherData
import json
from django.http import JsonResponse
from .decorators import role_required
from django.contrib.auth.decorators import login_required
from datetime import timedelta
from django.core.serializers.json import DjangoJSONEncoder


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
            time_to_sol = parse_duration_string(time_to_sol_raw)

            subj_id = request.POST.get('subj_test')
            subj = Subjects.objects.get(id=subj_id)

            description_test = request.POST.get('description_test', '')

            # Получение списков из формы
            points = json.loads(request.POST.get('point_solve', '[]'))
            expressions = json.loads(request.POST.get('user_expression', '[]'))
            answers = json.loads(request.POST.get('user_ans', '[]'))
            boolAns = json.loads(request.POST.get('user_bool_ans', '[]'))
            epsilons = json.loads(request.POST.get('user_eps', '[]'))
            types = json.loads(request.POST.get('user_type', '[]'))

            # Сохраняем тест
            test_slug = slugify(test_name)
            new_test = AboutTest.objects.create(
                name_tests=test_name,
                time_to_solution=time_to_sol,
                name_slug_tests=test_slug,
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
            return redirect('test_list')

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


@login_required
@role_required(['teacher', 'admin'])
def publish_test(request, slug):
    if request.method == "POST":
        test = get_object_or_404(AboutTest, name_slug_tests=slug)
        teacher = get_object_or_404(TeacherData, data_map=request.user)

        data = json.loads(request.body)
        group_ids = data.get('groups', [])

        print(test.id, teacher.id, group_ids)

        for group_id in group_ids:
            PublishedGroup.objects.create(
                test_name=test,
                teacher_name=teacher,
                group_name_id=group_id
            )

        test.is_published = 1
        test.save()

        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


# вот это в теории и на хуй не нужно, редачим через свойство value на странице в режиме редактирования
# @login_required
# @role_required(['teacher', 'admin'])
# def test_edit(request, slug_name):
#     test = get_object_or_404(AboutTest, name_slug_tests=slug_name)
#     QuestionFormSet = modelformset_factory(
#         AboutExpressions,
#         fields=('user_expression', 'user_ans', 'points_for_solve', 'user_eps', 'exist_select'),
#         extra=0
#     )
#
#     if request.method == 'POST':
#         formset = QuestionFormSet(request.POST, queryset=test.expressions.all())
#         if formset.is_valid():
#             formset.save()
#             return redirect('test_edit', slug=slug_name)
#     else:
#         formset = QuestionFormSet(queryset=test.expressions.all())
#
#     return render(request, 'editing_test.html', {
#         'test': test,
#         'formset': formset
#     })

