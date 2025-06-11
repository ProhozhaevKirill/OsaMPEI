from django.db import models
from create_tests.models import AboutExpressions, AboutTest
import datetime
from users.models import CustomUser


class StudentResult(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    test = models.ForeignKey(AboutTest, on_delete=models.CASCADE)
    attempt_number = models.PositiveIntegerField(default=1)
    result_points = models.FloatField()
    res_answer = models.CharField(max_length=255, blank=True)
    teacher_expressions = models.ManyToManyField(AboutExpressions)

    class Meta:
        unique_together = ('student', 'test', 'attempt_number')
