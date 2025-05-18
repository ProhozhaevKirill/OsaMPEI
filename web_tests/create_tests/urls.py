from django.urls import path
from . import views

app_name = 'create_tests'

urlpatterns = [
    path('', views.create_test, name='create_test'),
    path('listTests/', views.test_list, name='test_list'),
    path('listTests/<slug:slug_name>/', views.some_test, name='some_test'),
    path('publish-test/<slug:slug_name>/', views.publish_test, name='publish_test'),
    path('unpublish/<slug:slug_name>/', views.unpublish_test, name='unpublish_test'),
    path('delete-test/<slug:slug_name>/', views.delete_test, name='delete_test'),
    path('edit-test/<slug:slug_name>/', views.edit_test, name='edit_test'),
]
