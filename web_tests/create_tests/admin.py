from django.contrib import admin
from .models import Subjects, AboutExpressions, AboutTest, PublishedGroup, TypeAnswer

admin.site.register(Subjects)
admin.site.register(TypeAnswer)
admin.site.register(AboutExpressions)
admin.site.register(AboutTest)
admin.site.register(PublishedGroup)
