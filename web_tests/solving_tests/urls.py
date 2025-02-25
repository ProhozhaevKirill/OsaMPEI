from django.urls import path
from . import views

urlpatterns = [
    # Маршрут для списка тестов
    path('', views.list_test, name='list_test'),

    # Маршрут для прохождения теста
    path('<slug:slug_name>/', views.some_test_for_student, name='some_test_for_student'),

    # Маршрут для отображения результата
    path('result/', views.show_result, name='show_result'),
]
