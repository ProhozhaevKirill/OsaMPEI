from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from sympy.physics.units import current

from .forms import SignUpForm, EmailAuthenticationForm
from .models import WhiteList, CustomUser, StudentData, TeacherData, StudentGroup, StudentInstitute
from create_tests.models import AboutTest
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .decorators import role_required


def login_view(request):
    if request.method == 'POST':
        form = EmailAuthenticationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)

            if user is not None:
                login(request, user)
                # Получаем актуальные данные пользователя из БД
                user = CustomUser.objects.get(pk=user.pk)
                if hasattr(user, 'role'):
                    if user.role == 'student':
                        return redirect('account/')
                    elif user.role == 'teacher':
                        return redirect('TestsCreate/listTests/')
                return redirect('account/')  # Дефолтный редирект
            else:
                form.add_error(None, 'Неверный email или пароль.')
        return render(request, 'users/authentication.html', {'form': form})

    form = EmailAuthenticationForm()
    return render(request, 'users/authentication.html', {'form': form})


def register_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password1')

            # Проверка на существующий email
            if CustomUser.objects.filter(email=email).exists():
                form.add_error('email', 'Этот email уже зарегистрирован.')
                return render(request, 'users/registration.html', {'form': form})

            user = form.save(commit=False)

            if WhiteList.objects.filter(teacherMail=email).exists():
                user.role = 'teacher'
            else:
                user.role = 'student'

            user.email = email
            user.set_password(password)  # Хэширование пароля
            user.save()

            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                institutes = StudentInstitute.objects.all().prefetch_related('studentgroup_set')

                if hasattr(user, 'role') and user.role == 'teacher':
                    return render(request, 'users/teacher_account.html', {'institutes': institutes})
                else:
                    return render(request, 'users/reg_form_student.html', {'institutes': institutes})

    form = SignUpForm()
    return render(request, 'users/registration.html', {'form': form})


@login_required
@role_required(['student', 'admin'])
def form_registration(request):
    # Если данные уже есть - перенаправляем в кабинет
    if hasattr(request.user, 'studentdata'):
        return redirect('account_view')

    institutes = StudentInstitute.objects.all().prefetch_related('studentgroup_set')

    if request.method == "POST":

        try:
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            middle_name = request.POST.get('middle_name', '').strip()
            institute_id = request.POST.get('institute', '').strip()
            group_name = request.POST.get('group', '').strip()

            if not all([first_name, last_name, institute_id, group_name]):
                messages.error(request, "Заполните все обязательные поля!")
                return render(request, 'users/reg_form_student.html',
                              {'institutes': institutes})

            institute = StudentInstitute.objects.get(id=institute_id)

            group, created = StudentGroup.objects.get_or_create(
                name=group_name,
                name_inst=institute,
                defaults={'name': group_name, 'name_inst': institute}
            )

            StudentData.objects.update_or_create(
                data_map=request.user,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'middle_name': middle_name,
                    'institute': institute,
                    'group': group,
                    'training_status': True
                }
            )

            messages.success(request, "Данные успешно сохранены!")
            print("Данные успешно сохранены для пользователя", request.user.email)  # Логирование
            return redirect('account_view')

        except StudentInstitute.DoesNotExist:
            messages.error(request, "Выбранный институт не существует")
        except Exception as e:
            messages.error(request, f"Ошибка сохранения: {str(e)}")

    return render(request, 'users/reg_form_student.html',
                  {'institutes': institutes})


@login_required
@role_required(['student', 'admin'])
def account_view(request):
    current_user = request.user
    about_tests = AboutTest.objects.all()

    try:
        student_data = current_user.studentdata
    except StudentData.DoesNotExist:
        student_data = None

    return render(request, 'users/student_account.html', {
        'current_user': current_user,
        'student_data': student_data,
        'about_tests': about_tests
    })


@login_required
@role_required(['student', 'admin'])
def student_profile_view(request):
    try:
        student_data = request.user.studentdata
    except StudentData.DoesNotExist:
        messages.warning(request, "Пожалуйста, заполните ваш профиль перед продолжением")
        return redirect('form_registration')

    institutes = StudentInstitute.objects.all().prefetch_related('studentgroup_set')

    if request.method == "POST":
        # Валидация данных
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        middle_name = request.POST.get('middle_name', '').strip()
        institute_id = request.POST.get('institute', '').strip()
        group_name = request.POST.get('group', '').strip()

        # Проверка обязательных полей
        if not first_name or not last_name:
            messages.error(request, "Имя и фамилия обязательны для заполнения!")
            return render(request, 'users/student_profile.html', {
                'student_data': student_data,
                'institutes': institutes
            })

        if len(first_name) > 50 or len(last_name) > 50:
            messages.error(request, "Имя и фамилия не должны превышать 50 символов")
            return render(request, 'users/student_profile.html', {
                'student_data': student_data,
                'institutes': institutes
            })

        try:
            institute = StudentInstitute.objects.get(id=institute_id)

            group, created = StudentGroup.objects.get_or_create(
                name=group_name,
                name_inst=institute,
                defaults={'name': group_name, 'name_inst': institute}
            )

            # Обновление данных
            student_data.first_name = first_name
            student_data.last_name = last_name
            student_data.middle_name = middle_name if middle_name else None
            student_data.institute = institute
            student_data.group = group
            student_data.save()

            # Обновление связанных данных пользователя
            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.save()

            messages.success(request, "Профиль успешно обновлен!")
            return redirect('student_profile')

        except StudentInstitute.DoesNotExist:
            messages.error(request, "Выбранный институт не существует")
        except Exception as e:
            messages.error(request, f"Произошла ошибка: {str(e)}")
            # Логирование ошибки
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error updating student profile: {str(e)}")

    return render(request, 'users/student_profile.html', {
        'student_data': student_data,
        'institutes': institutes
    })


@login_required
@role_required(['student', 'admin'])
def material_view(request):
    return render(request, 'users/material.html')

