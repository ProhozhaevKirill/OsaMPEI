from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='index'),
    path('register/', views.register_view, name='register_view'),
    path('profile/', views.profile_view, name='profile'),
]
