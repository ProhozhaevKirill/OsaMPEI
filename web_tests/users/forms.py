from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import CustomUser, StudentData, TeacherData
from django.contrib.auth import authenticate


class SignUpForm(forms.ModelForm):
    email = forms.EmailField(required=True, label="Email")
    password1 = forms.CharField(label="Пароль", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Подтверждение пароля", widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ('email', 'password1', 'password2')

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 != password2:
            raise forms.ValidationError("Пароли не совпадают.")
        return cleaned_data

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


class ProfileForm(forms.ModelForm):
    class Meta:
        model = StudentData
        fields = [
            'first_name',
            'last_name',
            'middle_name',
            'photo',
            'institute',
            # 'direction',
            # 'department',
            'training_status',
            'group',
        ]
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'middle_name': 'Отчество',
            'photo': 'Фото профиля',
            'group': 'Группа',
        }
        widgets = {
            'photo': forms.FileInput(attrs={'accept': 'image/*'}),
        }


class TeacherProfileForm(forms.ModelForm):
    class Meta:
        model = TeacherData
        fields = [
            'first_name',
            'last_name',
            'middle_name',
            'photo',
            'institute',
        ]
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'middle_name': 'Отчество',
            'photo': 'Фото профиля',
            'institute': 'Институт',
        }
        widgets = {
            'photo': forms.FileInput(attrs={'accept': 'image/*'}),
        }
