from django.contrib import admin
from .models import CustomUser, StudentData, TeacherData, WhiteList, StudentGroup, StudentInstitute
# from .models import StudentDirection, StudentDepartment


admin.site.register(StudentInstitute)
# admin.site.register(StudentDirection)
# admin.site.register(StudentDepartment)
admin.site.register(StudentGroup)
admin.site.register(WhiteList)
admin.site.register(CustomUser)
admin.site.register(StudentData)
admin.site.register(TeacherData)
