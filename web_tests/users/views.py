from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from .forms import SignUpForm, EmailAuthenticationForm, ProfileForm, TeacherProfileForm
from .models import WhiteList, CustomUser, StudentData, TeacherData, StudentGroup, StudentInstitute
from create_tests.models import AboutTest, PublishedGroup
from solving_tests.models import StudentResult
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .decorators import role_required
from django.contrib.auth import logout as auth_logout
from create_tests.views import some_test


def login_view(request):
    if request.method == 'POST':
        form = EmailAuthenticationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].lower()  # Приводим к нижнему регистру
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)

            if user is not None:
                login(request, user)
                # Получаем актуальные данные пользователя из БД
                user = CustomUser.objects.get(pk=user.pk)
                if hasattr(user, 'role'):
                    if user.role == 'student':
                        return redirect('Home/')
                    elif user.role == 'teacher':
                        return redirect('TestsCreate/listTests/')
                return redirect('Home/')  # Дефолтный редирект
            else:
                form.add_error(None, 'Неверный email или пароль.')
        return render(request, 'users/authentication.html', {'form': form})

    form = EmailAuthenticationForm()
    return render(request, 'users/authentication.html', {'form': form})


def register_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email').lower()  # Приводим к нижнему регистру
            password = form.cleaned_data.get('password1')

            # Проверка на существующий email (с учетом регистра)
            if CustomUser.objects.filter(email__iexact=email).exists():
                form.add_error('email', 'Этот email уже зарегистрирован.')
                return render(request, 'users/registration.html', {'form': form})

            user = form.save(commit=False)

            if WhiteList.objects.filter(teacher_mail__iexact=email).exists():
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
    user = request.user
    context = {
        'current_user': user,
        'is_student': user.role == 'student',
    }

    if user.role == 'student':
        try:
            student_data = user.studentdata
        except StudentData.DoesNotExist:
            student_data = None

        institutes = StudentInstitute.objects.all()
        groups = StudentGroup.objects.all()

        if student_data and student_data.group:
            published_tests = AboutTest.objects.filter(
                publishedgroup__group_name=student_data.group
            ).distinct()
        else:
            published_tests = AboutTest.objects.none()

        # Получаем все результаты студента
        student_results = StudentResult.objects.filter(
            student=user,
            test__in=published_tests
        ).order_by('test', '-attempt_number')

        # Группируем по тесту: выбираем лучший результат по каждому тесту
        best_results = {}
        for result in student_results:
            if result.test_id not in best_results or result.result_points > best_results[result.test_id].result_points:
                best_results[result.test_id] = result

        # Обогащаем информацией: оставшиеся попытки, статус
        active_tests = []
        completed_tests = []
        for test in published_tests:
            all_attempts = [res for res in student_results if res.test_id == test.id]
            max_attempt = max([res.attempt_number for res in all_attempts], default=0)
            best_result = best_results.get(test.id)

            remaining_attempts = test.num_of_attempts - max_attempt

            test_info = {
                'test': test,
                'best_result': best_result,
                'remaining_attempts': remaining_attempts,
                'type_of_result': f"{best_result.result_points:.0f}" if best_result else None,
                'status': '',
            }

            if remaining_attempts <= 0:
                test_info['status'] = 'Завершено'
                completed_tests.append(test_info)
            else:
                test_info['status'] = f'Осталось {remaining_attempts} попыток'
                active_tests.append(test_info)

        # 1. Всего тестов
        total_tests = len(published_tests)

        # 2. Сколько решено (есть хотя бы одна попытка)
        solved_tests = len(set(result.test_id for result in student_results))

        # 3. Успеваемость на основе оценок
        def get_grade_weight(points):
            if points >= 90:
                return 1.0
            elif points >= 75:
                return 0.75
            elif points >= 60:
                return 0.5
            else:
                return 0.0

        # Собираем веса за каждый тест (0, если не решён)
        grade_weights = []
        for test in published_tests:
            best_result = best_results.get(test.id)
            if best_result:
                grade_weights.append(get_grade_weight(best_result.result_points))
            else:
                grade_weights.append(0.0)

        success_rate = int((sum(grade_weights) / total_tests) * 100) if total_tests > 0 else 0

        context.update({
            'total_tests': total_tests,
            'solved_tests': solved_tests,
            'success_rate': success_rate,
            'student_data': student_data,
            'institutes': institutes,
            'groups': groups,
            'about_tests': active_tests + completed_tests,
        })

    else:
        context['teacher_data'] = getattr(user, 'teacherdata', None)

    if request.method == 'POST':
        # Обработка обновления профиля
        user.email = request.POST.get('email', user.email)

        if user.role == 'student':
            if student_data is None:
                # Создаем, если не существует
                default_institute = StudentInstitute.objects.first()
                default_group = StudentGroup.objects.first()
                student_data = StudentData.objects.create(
                    data_map=user,
                    first_name='',
                    last_name='',
                    middle_name='',
                    institute=default_institute,
                    group=default_group,
                    training_status=True,
                    count_solve=0,
                    perc_of_correct_ans="0"
                )

            student_data.first_name = request.POST.get('first_name', student_data.first_name)
            student_data.last_name = request.POST.get('last_name', student_data.last_name)
            student_data.middle_name = request.POST.get('middle_name', student_data.middle_name)

            institute_id = request.POST.get('institute')
            if institute_id:
                student_data.institute = StudentInstitute.objects.get(id=institute_id)

            group_id = request.POST.get('group')
            if group_id:
                student_data.group = StudentGroup.objects.get(id=group_id)

            student_data.save()
        else:
            # Для учителей (если нужно)
            teacher_data = getattr(user, 'teacherdata', None)
            if teacher_data:
                teacher_data.first_name = request.POST.get('first_name', teacher_data.first_name)
                teacher_data.last_name = request.POST.get('last_name', teacher_data.last_name)
                teacher_data.middle_name = request.POST.get('middle_name', teacher_data.middle_name)
                teacher_data.save()

        user.save()
        return redirect('account_view')

    return render(request, 'users/student_account.html', context)


@login_required
@role_required(['teacher', 'admin'])
def account_view2(request):
    user = request.user
    context = {
        'current_user': user,
        'is_teacher': user.role == 'teacher',
    }

    try:
        teacher_data = user.teacherdata
    except TeacherData.DoesNotExist:
        teacher_data = None

    context['teacher_data'] = teacher_data

    if teacher_data:
        # Все тесты, созданные преподавателем
        teacher_tests = AboutTest.objects.filter(creator=teacher_data).order_by('-id')

        # Статистика
        created_tests_count = teacher_tests.count()
        published_tests_count = teacher_tests.filter(is_published=1).count()

        # Количество уникальных групп, где учит преподаватель (через PublishedGroup)
        students_count = PublishedGroup.objects.filter(teacher_name=teacher_data)\
                                              .values('group_name').distinct().count()

        context.update({
            'teacher_tests': teacher_tests,
        })

        # Динамические поля для шаблона
        teacher_data.created_tests_count = created_tests_count
        teacher_data.published_tests_count = published_tests_count
        teacher_data.students_count = students_count


    return render(request, 'users/teacher_account.html', context)


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
            logger.error(f"Ошибка обновления данных пользователей: {str(e)}")

    return render(request, 'users/student_profile.html', {
        'student_data': student_data,
        'institutes': institutes
    })


@login_required
@role_required(['student', 'admin'])
def data(request):
    user = request.user
    context = {}

    if user.role == 'student':
        default_institute = StudentInstitute.objects.first()
        default_group = StudentGroup.objects.first()

        data, created = StudentData.objects.get_or_create(
            data_map=user,
            defaults={
                'first_name': '',
                'last_name': '',
                'middle_name': '',
                'institute': default_institute,
                'group': default_group,
                'training_status': True,
                'count_solve': 0,
                'perc_of_correct_ans': "0"
            }
        )
        form = ProfileForm(instance=data)
    else:
        data, created = TeacherData.objects.get_or_create(
            data_map=user,
            defaults={
                'first_name': '',
                'last_name': '',
                'middle_name': ''
            }
        )
        form = TeacherProfileForm(instance=data)

    if request.method == 'POST':
        # Обработка удаления фото
        if 'delete_photo' in request.POST:
            if data.photo:
                data.photo.delete()
                data.photo = None
                data.save()
                messages.success(request, "Фото успешно удалено!")
                return redirect('data')

        user.email = request.POST.get('email', user.email)

        if user.role == 'student':
            form = ProfileForm(request.POST, request.FILES, instance=data)
            if form.is_valid():
                form.save()
                user.save()
                messages.success(request, "Профиль успешно обновлен!")
                return redirect('data')
        else:
            form = TeacherProfileForm(request.POST, request.FILES, instance=data)
            if form.is_valid():
                form.save()
                user.save()
                messages.success(request, "Профиль успешно обновлен!")
                return redirect('data')

    # Подготовка контекста
    context['user'] = user
    context['data'] = data
    context['form'] = form
    context['is_student'] = user.role == 'student'

    if user.role == 'student':
        context['institutes'] = StudentInstitute.objects.all()
        context['groups'] = StudentGroup.objects.all()

        student_group = data.group
        about_tests = AboutTest.objects.filter(
            publishedgroup__group_name=student_group,
            is_published=1
        ).distinct()
        context['about_tests'] = about_tests

    return render(request, 'users/student_data.html', context)


@login_required
@role_required(['student', 'admin'])
def material_view(request):
    return render(request, 'users/material.html')


@login_required
@role_required(['teacher', 'admin'])
def teacher_profile_view(request):
    user = request.user

    try:
        teacher_data = user.teacherdata
    except TeacherData.DoesNotExist:
        teacher_data = None

    if teacher_data is None:
        default_institute = StudentInstitute.objects.first()
        teacher_data = TeacherData.objects.create(
            data_map=user,
            first_name='',
            last_name='',
            middle_name='',
            institute=default_institute
        )

    institutes = StudentInstitute.objects.all()
    form = TeacherProfileForm(instance=teacher_data)

    if request.method == 'POST':
        # Обработка удаления фото
        if 'delete_photo' in request.POST:
            if teacher_data.photo:
                teacher_data.photo.delete()
                teacher_data.photo = None
                teacher_data.save()
                messages.success(request, "Фото успешно удалено!")
                return redirect('teacher_profile')

        # Обработка формы профиля
        form = TeacherProfileForm(request.POST, request.FILES, instance=teacher_data)
        if form.is_valid():
            user.email = request.POST.get('email', user.email)

            # Обновляем институт отдельно
            institute_id = request.POST.get('institute')
            if institute_id:
                teacher_data.institute = StudentInstitute.objects.get(id=institute_id)

            form.save()
            user.save()
            messages.success(request, "Профиль успешно обновлен!")
            return redirect('teacher_profile')

    context = {
        'user': user,
        'data': teacher_data,
        'form': form,
        'institutes': institutes,
    }

    return render(request, 'users/teacher_profile.html', context)


@login_required
def settings_view(request):
    """Страница настроек пользователя"""
    user = request.user

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'theme':
            # Обработка изменения темы
            theme = request.POST.get('theme')
            if theme == 'dark':
                user.theme = 'dark'
            else:
                user.theme = 'light'
            user.save()
            messages.success(request, f"Тема изменена на {'тёмную' if user.theme == 'dark' else 'светлую'}!")
        else:
            # Обработка изменения email
            new_email = request.POST.get('email', '').strip().lower()  # Приводим к нижнему регистру
            if new_email and new_email != user.email:
                if CustomUser.objects.filter(email__iexact=new_email).exclude(id=user.id).exists():
                    messages.error(request, "Этот email уже используется другим пользователем.")
                else:
                    user.email = new_email
                    user.save()
                    messages.success(request, "Email успешно обновлен!")

        return redirect('settings')

    context = {
        'user': user,
    }

    # Определяем шаблон в зависимости от роли
    if user.role == 'student':
        return render(request, 'users/settings_student.html', context)
    else:
        return render(request, 'users/settings_teacher.html', context)


@login_required
def help_view(request):
    """Страница помощи"""
    user = request.user

    context = {
        'user': user,
    }

    # Определяем шаблон в зависимости от роли
    if user.role == 'student':
        return render(request, 'users/help_student.html', context)
    else:
        return render(request, 'users/help_teacher.html', context)


@login_required
def logout_view(request):
    auth_logout(request)
    request.session.flush()
    response = redirect('/')
    response.delete_cookie('sessionid')
    return response
