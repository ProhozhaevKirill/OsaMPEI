from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView


urlpatterns = [
    path('', views.login_view, name='login_view'),
    path('register/', views.register_view, name='register_view'),
    path('logout/', LogoutView.as_view(next_page='//'), name='logout'),
    path('profile/', views.profile_view, name='profile'),
]
