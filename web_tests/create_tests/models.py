from email.policy import default
from django.db import models
from django.db.models import ForeignKey
from django.utils.text import slugify
from unidecode import unidecode
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from users.models import StudentGroup
from datetime import timedelta


class AboutExpressions(models.Model):
    user_expression = models.CharField(max_length=100, blank=False)
    user_ans = models.CharField(max_length=150, blank=False)
    true_ans = models.CharField(max_length=15, default='1')
    points_for_solve = models.IntegerField(default=1, blank=False)
    user_eps = models.CharField(max_length=150, default="0", blank=True)
    exist_select = models.BooleanField(default=False)

    def __str__(self):
        return self.user_expression

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class Subjects(models.Model):
    name = models.CharField(max_length=100, unique=True, default="Другое")

    def __str__(self):
        return self.name


class AboutTest(models.Model):
    objects = None
    name_tests = models.CharField(max_length=255, blank=False)  # Название теста
    time_to_solution = models.DurationField(default=timedelta(hours=1, minutes=30))
    name_slug_tests = models.SlugField(max_length=255, unique=True, db_index=True, verbose_name="URL")  # Слаг имени
    num_of_attempts = models.IntegerField(blank=True, default=1)  # Количество попыток для решения
    type_of_result = models.IntegerField(blank=True, default=1)  # Тип возвращаемого результата
    description = models.CharField(max_length=150, default="", blank=True)
    subj = models.ForeignKey(Subjects,
                             on_delete=models.PROTECT,
                             default=1)

    # publish_date = models.DateTimeField(auto_now_add=True)  # Дата публикации (можно будет отложить публикацию)
    # expiration_date = models.DateTimeField(null=True, blank=True)  # Время публикации (аналогично)
    # time_last_change = models.DateTimeField(auto_now=True)  # Время последнего изменения теста
    expressions = models.ManyToManyField(AboutExpressions)

    def __str__(self):
        return self.name_tests

    def save(self, *args, **kwargs):
        if not self.id:  # Проверка на создание нового объекта
            self.name_slug_tests = slugify(unidecode(self.name_tests))
        super().save(*args, **kwargs)


class PublishedGroup(models.Model):
    group_name = ForeignKey(StudentGroup, on_delete=models.PROTECT)
    test_name = ForeignKey(AboutTest, on_delete=models.PROTECT)
    is_published = models.BooleanField(default=False)


@receiver(pre_delete, sender=AboutTest)
def delete_related_expressions(sender, instance, **kwargs):
    instance.expressions.clear()

