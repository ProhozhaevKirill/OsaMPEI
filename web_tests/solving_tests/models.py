from django.db import models
from create_tests.models import AboutExpressions

class StudentResult(models.Model):
    accuracy = models.FloatField(max_length=255)
    resAnswer = models.CharField(max_length=255, blank=True)
    teacherExpressions = models.ManyToManyField(AboutExpressions)
    
    def __str__(self):
        return self.resAnswer