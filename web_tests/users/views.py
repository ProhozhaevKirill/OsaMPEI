from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from sympy.testing.runtests import method
from .forms import SignUpForm, EmailAuthenticationForm
from .models import WhiteList, CustomUser, StudentData, TeacherData, StudentGroup, StudentInstitute
# from .models import StudentDirection, StudentDepartment
import random as rnd
from django.contrib import messages


def login_view(request):
    if request.method == 'POST':
        form = EmailAuthenticationForm(request.POST)  # Убираем request
        if form.is_valid():  # Проверка валидности формы
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(username=email, password=password)  # Используем email как username

            if user is not None:
                login(request, user)
                return redirect('list_test')
            else:
                form.add_error(None, 'Неверный email или пароль.')  # Ошибка, если аутентификация не удалась

        # Если форма не валидна, возвращаем её с ошибками
        return render(request, 'users/authentication.html', {'form': form})
    else:
        form = EmailAuthenticationForm()

    return render(request, 'users/authentication.html', {'form': form})


def register_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            email = form.cleaned_data.get('email')

            # Проверка на уникальность email
            if CustomUser.objects.filter(email=email).exists():
                form.add_error('email', 'Этот email уже зарегистрирован.')
                return render(request, 'users/registration.html', {'form': form})

            # Проверка наличия в WhiteList
            if WhiteList.objects.filter(teacherMail=email).exists():
                user.role = 'teacher'
            else:
                user.role = 'student'

                # Для будущей валидации с использованием почтового сервера
                # random_mail_code = rnd.randint(1000, 9999)
                # print(random_mail_code)

            user.email = email
            user.save()

            login(request, user)
            if user.role == 'teacher':
                return render(request, 'users/profile_for_teacher.html')
            else:
                return render(request, 'users/profile_for_student.html')

                # Для будущей валидации с использованием почтового сервера
                # request.session['mail_code'] = random_mail_code
                # return render(request, 'users/profile_for_student.html', {'random_mail_code': random_mail_code})

                # return render(request, 'users/profile_for_student.html', {'random_mail_code': random_mail_code})
    else:
        form = SignUpForm()
    return render(request, 'users/registration.html', {'form': form})


# def profile_view(request):
#     if request.user.role == 'teacher':
#         # Для будущей страницы с заполнением данных мб или знакомство с сервисом
#         if request.method == "POST":
#             pass
#         return render(request, 'users/profile_for_teacher.html')
#
#     else:
#         if request.method == "POST":
#             first_name = request.POST.get('first_name')
#             last_name = request.POST.get('last_name')
#             middle_name = request.POST.get('middle_name')
#             # institute = request.POST.get('institute')
#             group = request.POST.get('group')
#
#             institute_id = request.POST.get('institute')
#             try:
#                 institute = StudentInstitute.objects.get(id=institute_id)
#             except StudentInstitute.DoesNotExist:
#                 messages.error(request, "Институт не найдена.")
#                 return redirect('profile')
#
#             # direction_id = request.POST.get('direction')
#             # try:
#             #     direction = StudentDirection.objects.get(id=direction_id)
#             # except StudentDirection.DoesNotExist:
#             #     messages.error(request, "Направление не найдено.")
#             #     return redirect('profile')
#             #
#             # department_id = request.POST.get('department')
#             # try:
#             #     department = StudentDepartment.objects.get(id=department_id)
#             # except StudentDepartment.DoesNotExist:
#             #     messages.error(request, "Кафедра не найдена.")
#             #     return redirect('profile')
#
#             # group_id = request.POST.get('group')
#             # try:
#             #     group = StudentGroup.objects.get(id=group_id)
#             # except StudentGroup.DoesNotExist:
#             #     messages.error(request, "Группа не найдена.")
#             #     return redirect('profile')
#
#             new_student = StudentData.objects.create(
#                 first_name=first_name,
#                 last_name=last_name,
#                 middle_name=middle_name,
#                 institute=institute,
#                 # direction=direction,
#                 # department=department,
#                 group=group,
#                 data_map=request.user
#             )
#
#             # print('hui', first_name, last_name, middle_name, institute, group)
#
#             new_student.save()
#
#             return redirect('list_test')
#
#             # Для будущей валидации с использованием почтового сервера
#             # input_code = request.POST.get('code-mpei')
#
#             # count = 0
#             # session_code = request.session.get('mail_code')
#             # if input_code and int(input_code) == session_code:
#             #     return render(request, 'users/profile_for_student.html')
#             # else:
#             #     count += 1
#             #     messages.error(request, "Неверный код подтверждения. Попробуйте ещё раз.")
#             #     if count == 3:
#             #         return redirect('profile')
#
#         return render(request, 'users/profile_for_student.html')


from django.contrib.auth.decorators import login_required

@login_required
def profile_view(request):
    if request.user.role == 'teacher':
        return render(request, 'users/profile_for_teacher.html')
    else:
        institutes = StudentInstitute.objects.all()  # Получаем все институты для формы

        if request.method == "POST":
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            middle_name = request.POST.get('middle_name')
            institute_id = request.POST.get('institute')
            group_name = request.POST.get('group')

            # Валидация данных
            if not all([first_name, last_name, institute_id, group_name]):
                messages.error(request, "Пожалуйста, заполните все обязательные поля.")
                return render(request, 'users/profile_for_student.html', {'institutes': institutes})

            try:
                institute = StudentInstitute.objects.get(id=institute_id)
                group, created = StudentGroup.objects.get_or_create(name=group_name)

                # Создаем или обновляем данные студента
                student_data, created = StudentData.objects.update_or_create(
                    data_map=request.user,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'middle_name': middle_name,
                        'institute': institute,
                        'group': group
                    }
                )

                messages.success(request, "Данные успешно сохранены!")
                return redirect('list_test')

            except StudentInstitute.DoesNotExist:
                messages.error(request, "Выбранный институт не существует.")
                return render(request, 'users/profile_for_student.html', {'institutes': institutes})

        return render(request, 'users/profile_for_student.html', {'institutes': institutes})