from django.urls import path
from . import views

app_name = 'create_tests'

urlpatterns = [
    path('', views.create_test, name='create_test'),
    path('listTests/', views.test_list, name='test_list'),
    path('listTests/<slug:slug_name>/', views.some_test, name='some_test'),
    path('solve-test/<slug:slug_name>/', views.solve_test_teacher, name='solve_test'),
    path('solve-test/<slug:slug_name>/result/', views.show_result_teacher, name='show_result_teacher'),
    path('publish-test/<slug:slug_name>/', views.publish_test, name='publish_test'),
    path('unpublish/<slug:slug_name>/', views.unpublish_test, name='unpublish_test'),
    path('delete-test/<slug:slug_name>/', views.delete_test, name='delete_test'),
    path('edit-test/<slug:slug_name>/', views.edit_test, name='edit_test'),
    path('save-group-set/', views.save_group_set, name='save_group_set'),
    path('get-group-lists/', views.get_group_lists, name='get_group_lists'),
    path('get-group-list/<int:list_id>/', views.get_group_list, name='get_group_list'),
    path('delete-group-list/<int:list_id>/', views.delete_group_list, name='delete_group_list'),
]
