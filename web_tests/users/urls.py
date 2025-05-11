from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView


urlpatterns = [
    path('', views.login_view, name='login_view'),  # Вход в систему
    path('register/', views.register_view, name='register_view'),  # Регистрация непосредственно
    path('logout/', LogoutView.as_view(next_page='//'), name='logout'),  # Выход из системы
    path('form_registration/', views.form_registration, name='form_registration'),  # Форма для заполнения при регистрации
    path('Home/', views.account_view, name='account_view'),  # Личный кабинет студента
    path('personaInf/', views.account_view2, name='account_view2'),
    path('data/', views.data, name='data'),
    path('material/', views.material_view, name='material'),  # Дополнительные материалы
]
