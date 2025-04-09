from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import CustomUser
from django.contrib.auth import authenticate


class SignUpForm(forms.ModelForm):
    email = forms.EmailField(required=True, label="Email")
    password1 = forms.CharField(label="Пароль", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Подтверждение пароля", widget=forms.PasswordInput)

    class Meta:
        model = CustomUser  # Используем CustomUser, а не стандартный User
        fields = ('email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)

        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()
        return user


class EmailAuthenticationForm(forms.Form):
    email = forms.EmailField(label="Почта (ОСЭП)", required=True)
    password = forms.CharField(widget=forms.PasswordInput, label="Пароль", required=True)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if email and password:
            # Попытка аутентификации с использованием почты
            user = authenticate(username=email, password=password)  # Используем email как username
            if user is None:
                raise forms.ValidationError("Неверная почта или пароль.")
        return cleaned_data


class CustomAuthenticationForm(AuthenticationForm):
    email = forms.EmailField(label="Почта (ОСЭП)")
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"placeholder": "Введите ваш пароль"})
    )

