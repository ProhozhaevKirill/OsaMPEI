from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.login_view, name='login_view'),
    path('register/', views.register_view, name='register_view'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),

    path('form_registration/', views.form_registration, name='form_registration'),
    path('Home/', views.account_view, name='account_view'),
    path('personaInf/', views.account_view2, name='account2'),
    path('teacher_profile/', views.teacher_profile_view, name='teacher_profile'),
    path('data/', views.data, name='data'),
    path('material/', views.material_view, name='material'),
    path('settings/', views.settings_view, name='settings'),
    path('help/', views.help_view, name='help'),
]
