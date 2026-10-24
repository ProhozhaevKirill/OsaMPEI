from django.urls import path
from . import views
from . import attempt_views

app_name = 'solving_tests'

urlpatterns = [
    path('', views.list_test, name='list_test'),
    path('<slug:slug_name>/start/', attempt_views.new_attempt, name='new_attempt'),
    path('<slug:slug_name>/attempt/<int:attempt_id>/', attempt_views.attempt_api, name='attempt_api'),
    path('<slug:slug_name>/attempt/<int:attempt_id>/result/', attempt_views.attempt_result, name='attempt_result'),
    path('<slug:slug_name>/', views.some_test_for_student, name='some_test_for_student'),
    path('<slug:slug_name>/result/', views.show_result, name='show_result'),
    path('<slug:slug_name>/view-result/', views.view_completed_result, name='view_completed_result'),
]
