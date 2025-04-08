from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")
    role = forms.CharField()

    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)
        self.fields['username'].label = "Имя пользователя"
        self.fields['email'].label = "Электронная почта"
        self.fields['role'].label = "Роль для доступа"
        self.fields['password1'].label = "Пароль"
        self.fields['password2'].label = "Подтверждение пароля"


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Логин",
        widget=forms.TextInput(attrs={"placeholder": "Введите ваш логин"}),
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"placeholder": "Введите ваш пароль"}),
    )