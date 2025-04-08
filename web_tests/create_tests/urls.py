from django.urls import path
from . import views

urlpatterns = [
    path('', views.create_test, name='create_test'),
    path('listTests/', views.test_list, name='test_list'),
    # path('editingTests/<int:id_test>/', views.editing_test, name='editing_test'),
    path('listTests/<slug:slug_name>/', views.some_test, name='some_test'),
    path('delete-test/<slug:slug>/', views.delete_test, name='delete_test'),
]
