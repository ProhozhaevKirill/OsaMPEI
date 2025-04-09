from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .forms import SignUpForm, EmailAuthenticationForm
from .models import WhiteList, CustomUser


from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from .forms import EmailAuthenticationForm

def login_view(request):
    if request.method == 'POST':
        form = EmailAuthenticationForm(request.POST)  # Убираем request
        if form.is_valid():  # Проверка валидности формы
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(username=email, password=password)  # Используем email как username

            if user is not None:
                login(request, user)
                return redirect('mapping') # Временно маршрутизаторы
                # return redirect('profile')  # Перенаправление на страницу профиля после успешного входа
            else:
                form.add_error(None, 'Неверный email или пароль.')  # Ошибка, если аутентификация не удалась

        # Если форма не валидна, возвращаем её с ошибками
        return render(request, 'users/authentication.html', {'form': form})
    else:
        form = EmailAuthenticationForm()  # Создание пустой формы для GET запроса

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

            user.email = email
            user.set_password(form.cleaned_data['password1'])  # Зашифровываем пароль
            user.save()  # Сохраняем пользователя

            login(request, user)
            return redirect('mapping')  # Временно маршрутизаторы
            # return redirect('profile')  # Перенаправление на страницу профиля после успешного входа
    else:
        form = SignUpForm()
    return render(request, 'users/registration.html', {'form': form})


def profile_view(request):
    if request.user.role == 'teacher':
        return render(request, 'users/profile_for_teacher.html')
    else:
        return render(request, 'users/profile_for_student.html')


# Временный маршрутизатор
def testing_role(request):
    if request.user.role == 'teacher':
        return render(request, 'users/temperary_page_t.html')
    else:
        return render(request, 'users/temperary_page_s.html')
