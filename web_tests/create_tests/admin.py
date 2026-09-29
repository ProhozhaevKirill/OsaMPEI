from django.contrib import admin
from .models import Subjects, AboutExpressions, AboutTest, PublishedGroup, TypeAnswer, TypeNorm

admin.site.register(Subjects)
admin.site.register(TypeAnswer)
admin.site.register(TypeNorm)
admin.site.register(AboutExpressions)


@admin.register(AboutTest)
class AboutTestAdmin(admin.ModelAdmin):
    list_display = ('name_tests', 'subj', 'creator', 'is_published', 'publish_from', 'publish_until')
    list_filter = ('is_published', 'subj')
    search_fields = ('name_tests', 'creator__last_name', 'creator__data_map__email')


@admin.register(PublishedGroup)
class PublishedGroupAdmin(admin.ModelAdmin):
    list_display = ('test_name', 'group_name', 'teacher_name')
    search_fields = ('test_name__name_tests', 'group_name__name', 'teacher_name__last_name')
