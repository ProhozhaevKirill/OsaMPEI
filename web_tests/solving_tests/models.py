from django.db import models
from create_tests.models import AboutExpressions, AboutTest, TaskGroup, TaskVariant
import datetime
from users.models import CustomUser
from django.utils import timezone


class StudentResult(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    test = models.ForeignKey(AboutTest, on_delete=models.CASCADE)
    attempt_number = models.PositiveIntegerField(default=1)
    result_points = models.FloatField()
    max_points = models.FloatField(default=0)  # Максимально возможные баллы
    percentage_score = models.FloatField(default=0)  # Процент выполнения
    res_answer = models.CharField(max_length=255, blank=True)
    teacher_expressions = models.ManyToManyField(AboutExpressions, blank=True)

    # Дополнительные поля для подробного результата
    started_at = models.DateTimeField(default=timezone.now)  # Время начала
    completed_at = models.DateTimeField(null=True, blank=True)  # Время завершения
    time_spent = models.DurationField(null=True, blank=True)  # Время выполнения
    is_completed = models.BooleanField(default=False)  # Завершен ли тест

    class Meta:
        unique_together = ('student', 'test', 'attempt_number')
        ordering = ['-completed_at', '-started_at']

    def __str__(self):
        return f"{self.student.email} - {self.test.name_tests} (попытка {self.attempt_number})"

    def save(self, *args, **kwargs):
        # Автоматический расчет процента
        if self.max_points > 0:
            self.percentage_score = (self.result_points / self.max_points) * 100
        super().save(*args, **kwargs)


class StudentTaskGroupResult(models.Model):
    """Результаты по группам заданий"""
    student_result = models.ForeignKey(StudentResult, on_delete=models.CASCADE, related_name='group_results')
    task_group = models.ForeignKey(TaskGroup, on_delete=models.CASCADE)
    points_earned = models.FloatField(default=0)
    max_points = models.FloatField(default=0)

    class Meta:
        unique_together = ('student_result', 'task_group')

    def __str__(self):
        return f"Группа {self.task_group.number} - {self.points_earned}/{self.max_points}"


class StudentTaskAnswer(models.Model):
    """Ответы студентов на конкретные задания"""
    student_result = models.ForeignKey(StudentResult, on_delete=models.CASCADE, related_name='task_answers')
    task_variant = models.ForeignKey(TaskVariant, on_delete=models.CASCADE, null=True, blank=True)
    expression = models.ForeignKey(AboutExpressions, on_delete=models.CASCADE, null=True, blank=True)
    student_answer = models.CharField(max_length=500, blank=True)
    is_correct = models.BooleanField(default=False)
    points_earned = models.FloatField(default=0)
    max_points = models.FloatField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=['student_result', 'task_variant']),
            models.Index(fields=['student_result', 'expression']),
        ]

    def __str__(self):
        task_name = self.task_variant or self.expression
        return f"Ответ на {task_name} - {self.points_earned}/{self.max_points}"
