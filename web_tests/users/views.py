from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .forms import SignUpForm


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')  # Исправляем login -> username
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('profile')
    else:
        form = AuthenticationForm()
    return render(request, 'users/authentication.html', {'form': form})


def register_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Автоматически заходим
            return redirect('profile')  # Перенаправляем на профиль
    else:
        form = SignUpForm()
    return render(request, 'users/registration.html', {'form': form})


def profile_view(request):
    return render(request, 'users/profile_for_student.html')
