from django.db import models
from create_tests.models import AboutExpressions
import datetime
# from users.models import CustomUser


class StudentResult(models.Model):
    # student = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    resultPoints = models.FloatField(max_length=255)
    allResAnswer = models.CharField(max_length=255, blank=True)
    teacherExpressions = models.ManyToManyField(AboutExpressions)

    def __str__(self):
        return self.allResAnswer