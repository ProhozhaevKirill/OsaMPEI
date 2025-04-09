from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=[('student', 'Student'), ('teacher', 'Teacher')])

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    # Устанавливаем get_username
    def get_username(self):
        return self.email

    # Указываем значение по умолчанию для существующих записей
    username = models.CharField(max_length=150, default='default_username')


class WhiteList(models.Model):
    teacherMail = models.EmailField(unique=True)

    def __str__(self):
        return self.teacherMail
