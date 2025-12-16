from django.urls import path
from . import views

app_name = 'solving_tests'

urlpatterns = [
    path('', views.list_test, name='list_test'),
    path('<slug:slug_name>/', views.some_test_for_student, name='some_test_for_student'),
    path('<slug:slug_name>/result/', views.show_result, name='show_result'),
    path('<slug:slug_name>/view-result/', views.view_completed_result, name='view_completed_result'),
]
