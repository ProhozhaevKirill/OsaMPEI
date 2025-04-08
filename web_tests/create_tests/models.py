from django.db import models
from django.utils.text import slugify
from unidecode import unidecode
from django.db.models.signals import pre_delete
from django.dispatch import receiver


class AboutExpressions(models.Model):
    user_expression = models.CharField(max_length=100, blank=False)
    user_ans = models.CharField(max_length=150, blank=False)
    true_ans = models.CharField(max_length=15, default='1')
    points_for_solve = models.IntegerField(default=1, blank=False)
    user_eps = models.CharField(max_length=150, default="0", blank=True)
    user_type = models.CharField(default='float', max_length=20, blank=True)
    exist_select = models.BooleanField(default=False)  # Добавлено поле для вариантов ответа

    def __str__(self):
        return self.user_expression

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class AboutTest(models.Model):
    objects = None
    name_tests = models.CharField(max_length=255, blank=False)  # Название теста
    time_to_solution = models.CharField(max_length=20, default='90')  # Продолжительность в минутах как строка
    is_published = models.BooleanField(default=False)  # Опубликовано / не опубликовано
    name_slug_tests = models.SlugField(max_length=255, unique=True, db_index=True, verbose_name="URL")  # Слаг имени
    # time_last_change = models.DateTimeField(auto_now=True)  # Время последнего изменения теста
    expressions = models.ManyToManyField(AboutExpressions)

    def __str__(self):
        return self.name_tests

    def save(self, *args, **kwargs):
        if not self.id:  # Проверка на создание нового объекта
            self.name_slug_tests = slugify(unidecode(self.name_tests))
        super().save(*args, **kwargs)


@receiver(pre_delete, sender=AboutTest)
def delete_related_expressions(sender, instance, **kwargs):
    instance.expressions.clear()