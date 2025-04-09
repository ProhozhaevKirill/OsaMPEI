from django.contrib import admin
from .models import WhiteList

# Регистрируем модель WhiteList в админке
admin.site.register(WhiteList)
