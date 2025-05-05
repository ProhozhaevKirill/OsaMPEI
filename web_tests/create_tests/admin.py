from django.contrib import admin
from .models import Subjects, AboutExpressions, AboutTest, PublishedGroup

admin.site.register(Subjects)
admin.site.register(AboutExpressions)
admin.site.register(AboutTest)
admin.site.register(PublishedGroup)
