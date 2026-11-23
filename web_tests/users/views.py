from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone
from .forms import SignUpForm, EmailAuthenticationForm, ProfileForm, TeacherProfileForm
from .models import WhiteList, CustomUser, StudentData, TeacherData, StudentGroup, StudentInstitute
from create_tests.models import AboutTest, PublishedGroup
from solving_tests.models import FreeAnswerGrade, StudentResult, TestAttempt
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .decorators import role_required, anonymous_required
from django.contrib.auth import logout as auth_logout
from create_tests.views import some_test


def fix_user_roles(request):
    """Временная функция для исправления ролей пользователей"""
    from django.http import HttpResponse

    users_fixed = 0
    for user in CustomUser.objects.filter(role__isnull=True).union(
        CustomUser.objects.filter(role='')
    ):
        if WhiteList.objects.filter(teacher_mail__iexact=user.email).exists():
            user.role = 'teacher'
        else:
            user.role = 'student'
        user.save()
        users_fixed += 1
        print(f"Fixed role for {user.email}: {user.role}")

    return HttpResponse(f"Fixed {users_fixed} users")


@anonymous_required
def login_view(request):
    print(f"DEBUG login_view: path={request.path}, method={request.method}, authenticated={request.user.is_authenticated}")
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
                        return redirect('/Home/')
                    elif user.role == 'teacher':
                        return redirect('/TestsCreate/listTests/')
                return redirect('/Home/')  # Дефолтный редирект
            else:
                form.add_error(None, 'Неверный email или пароль.')
        return render(request, 'users/authentication.html', {'form': form})

    form = EmailAuthenticationForm()
    return render(request, 'users/authentication.html', {'form': form})


@anonymous_required
def register_view(request):
    if request.method == 'POST':
        # Проверка на повторную отправку формы
        if 'pending_registration' in request.session:
            messages.warning(request, "Регистрация уже начата. Завершите заполнение данных.")
            institutes = StudentInstitute.objects.all()
            groups = StudentGroup.objects.all()
            if request.session['pending_registration']['is_teacher']:
                return render(request, 'users/teacher_registration.html', {'institutes': institutes})
            else:
                return render(request, 'users/reg_form_student.html', {'institutes': institutes, 'groups': groups})

        form = SignUpForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email').lower()  # Приводим к нижнему регистру
            password = form.cleaned_data.get('password1')

            # Проверка на существующий email (с учетом регистра)
            if CustomUser.objects.filter(email__iexact=email).exists():
                form.add_error('email', 'Этот email уже зарегистрирован.')
                return render(request, 'users/registration.html', {'form': form})

            # Сохраняем данные в сессии для последующего использования
            request.session['pending_registration'] = {
                'email': email,
                'password': password,
                'is_teacher': WhiteList.objects.filter(teacher_mail__iexact=email).exists()
            }

            institutes = StudentInstitute.objects.all()
            groups = StudentGroup.objects.all()

            if request.session['pending_registration']['is_teacher']:
                return render(request, 'users/teacher_registration.html', {'institutes': institutes})
            else:
                return render(request, 'users/reg_form_student.html', {'institutes': institutes, 'groups': groups})

    form = SignUpForm()
    return render(request, 'users/registration.html', {'form': form})


def form_registration(request):
    # Проверяем, есть ли данные регистрации в сессии
    if 'pending_registration' not in request.session:
        messages.error(request, "Сессия регистрации истекла. Пожалуйста, зарегистрируйтесь заново.")
        return redirect('register_view')

    # Если пользователь уже авторизован и имеет данные - перенаправляем
    if request.user.is_authenticated and hasattr(request.user, 'studentdata'):
        return redirect('account_view')

    institutes = StudentInstitute.objects.all()
    groups = StudentGroup.objects.all()

    if request.method == "POST":
        try:
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            middle_name = request.POST.get('middle_name', '').strip()
            institute_id = request.POST.get('institute', '').strip()
            group_id = request.POST.get('group', '').strip()

            if not all([first_name, last_name, institute_id, group_id]):
                messages.error(request, "Заполните все обязательные поля!")
                return render(request, 'users/reg_form_student.html',
                              {'institutes': institutes, 'groups': groups})

            institute = StudentInstitute.objects.get(id=institute_id)
            group = StudentGroup.objects.get(id=group_id, name_inst=institute)

            # Теперь создаем пользователя в БД
            pending_data = request.session['pending_registration']

            user = CustomUser.objects.create_user(
                email=pending_data['email'],
                password=pending_data['password'],
                role='teacher' if pending_data['is_teacher'] else 'student'
            )

            # Создаем данные студента
            StudentData.objects.create(
                data_map=user,
                first_name=first_name,
                last_name=last_name,
                middle_name=middle_name,
                institute=institute,
                group=group,
                training_status=True
            )

            # Очищаем сессию
            del request.session['pending_registration']

            # Авторизуем пользователя напрямую (без повторного authenticate)
            user.backend = 'users.backends.CaseInsensitiveEmailBackend'
            login(request, user)
            messages.success(request, "Регистрация завершена успешно!")
            return redirect('account_view')

        except StudentInstitute.DoesNotExist:
            messages.error(request, "Выбранный институт не существует")
        except StudentGroup.DoesNotExist:
            messages.error(request, "Выбранная группа не существует")
        except Exception as e:
            messages.error(request, f"Ошибка регистрации: {str(e)}")

    return render(request, 'users/reg_form_student.html',
                  {'institutes': institutes, 'groups': groups})


def form_registration_teacher(request):
    # Проверяем, есть ли данные регистрации в сессии
    if 'pending_registration' not in request.session:
        messages.error(request, "Сессия регистрации истекла. Пожалуйста, зарегистрируйтесь заново.")
        return redirect('register_view')

    # Проверяем, что пользователь действительно учитель
    if not request.session['pending_registration']['is_teacher']:
        messages.error(request, "Доступ запрещен.")
        return redirect('register_view')

    institutes = StudentInstitute.objects.all()

    if request.method == "POST":
        try:
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            middle_name = request.POST.get('middle_name', '').strip()
            institute_id = request.POST.get('institute', '').strip()

            if not all([first_name, last_name, institute_id]):
                messages.error(request, "Заполните все обязательные поля!")
                return render(request, 'users/teacher_registration.html',
                              {'institutes': institutes})

            institute = StudentInstitute.objects.get(id=institute_id)

            # Создаем пользователя в БД
            pending_data = request.session['pending_registration']

            user = CustomUser.objects.create_user(
                email=pending_data['email'],
                password=pending_data['password'],
                role='teacher'
            )

            # Создаем данные преподавателя
            TeacherData.objects.create(
                data_map=user,
                first_name=first_name,
                last_name=last_name,
                middle_name=middle_name,
                institute=institute
            )

            # Очищаем сессию
            del request.session['pending_registration']

            # Авторизуем пользователя напрямую
            user.backend = 'users.backends.CaseInsensitiveEmailBackend'
            login(request, user)
            messages.success(request, "Регистрация завершена успешно!")
            return redirect('/TestsCreate/listTests/')

        except StudentInstitute.DoesNotExist:
            messages.error(request, "Выбранный институт не существует")
        except Exception as e:
            messages.error(request, f"Ошибка регистрации: {str(e)}")

    return render(request, 'users/teacher_registration.html',
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

        now = timezone.now()
        pending_grades = FreeAnswerGrade.objects.filter(
            student_result_id=OuterRef('pk'), is_correct__isnull=True,
        )
        results = StudentResult.objects.filter(student=user, test__in=published_tests).annotate(
            pending_review=Exists(pending_grades),
        ).order_by('-percentage_score', '-attempt_number', '-pk')

        best_results = {}
        attempt_numbers = {}
        awaiting_review = set()
        for result in results:
            test_id = result.test_id
            attempt_numbers[test_id] = max(attempt_numbers.get(test_id, 0), result.attempt_number)
            if result.pending_review:
                awaiting_review.add(test_id)
            else:
                best_results.setdefault(test_id, result)

        unfinished = {
            attempt.test_id: attempt
            for attempt in TestAttempt.objects.filter(
                student=user, test__in=published_tests, result__isnull=True,
            ).order_by('attempt_number')
        }

        active_tests = []
        completed_tests = []
        performance_scores = []
        for test in published_tests:
            best = best_results.get(test.pk)
            percentage = min(100, max(0, best.percentage_score)) if best else None
            attempts_used = attempt_numbers.get(test.pk, 0)
            current_attempt = unfinished.get(test.pk)
            remaining = max(0, test.num_of_attempts - attempts_used)
            has_attempts = test.num_of_attempts <= 0 or remaining > 0
            expired = test.publish_until is not None and test.publish_until <= now
            waiting = test.pk in awaiting_review or (
                current_attempt is not None
                and (current_attempt.submitted_at is not None or current_attempt.deadline <= now)
            )
            missed = bool(test.is_published and expired and not attempts_used and current_attempt is None)

            grade = None
            if percentage is not None:
                grade = (5 if percentage >= test.grade_5_threshold else
                         4 if percentage >= test.grade_4_threshold else
                         3 if percentage >= test.grade_3_threshold else 2)
            elif missed:
                grade = 0

            if missed:
                status = 'Пропущен'
                performance_scores.append(0)
            elif current_attempt is not None and not waiting:
                status = 'Начат'
            elif waiting:
                status = 'На проверке'
            elif expired or not has_attempts:
                status = 'Завершено'
            elif not test.is_available_now(now):
                status = 'Пока недоступен'
            elif test.num_of_attempts <= 0:
                status = 'Попытки не ограничены'
            else:
                status = f'Осталось попыток: {remaining}'

            if percentage == 100 or (
                percentage is not None and current_attempt is None and not waiting
                and (expired or not has_attempts)
            ):
                performance_scores.append(percentage)

            info = {'test': test, 'grade': grade, 'status': status}
            if status in ('Завершено', 'Пропущен'):
                completed_tests.append(info)
            else:
                active_tests.append(info)

        total_tests = len(published_tests)
        solved_tests = len(attempt_numbers)
        success_rate = round(sum(performance_scores) / len(performance_scores)) if performance_scores else 0

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

        # Queue every ungraded attempt; scoring one must not hide its siblings.
        from django.db.models import Exists, OuterRef
        from solving_tests.models import FreeAnswerGrade
        pending_results = StudentResult.objects.filter(test__creator=teacher_data).filter(
            Exists(FreeAnswerGrade.objects.filter(
                student_result_id=OuterRef('pk'), is_correct__isnull=True))
        ).select_related('test', 'student', 'student__studentdata').order_by('-completed_at', '-pk')

        context.update({
            'teacher_tests': teacher_tests,
            'pending_results': pending_results,
            'pending_results_count': pending_results.count(),
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
