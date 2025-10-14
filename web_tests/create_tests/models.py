from email.policy import default
from django.db import models
from django.db.models import ForeignKey
from django.utils.text import slugify
from unidecode import unidecode
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from users.models import StudentGroup, TeacherData
from datetime import timedelta


class TypeAnswer(models.Model):
    TYPE_CHOICES = [
        (1, "Целые"),
        (2, "Нецелые"),
        (3, "Строки"),
        (4, "Матрицы"),
    ]

    type_code = models.IntegerField(choices=TYPE_CHOICES, unique=True)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class TypeNorm(models.Model):
    TYPE_CHOICES_NORM = [
        (1, "Евклидова норма"),
        (2, "Первая норма"),
        (3, "Бесконечная норма"),
    ]

    type_code = models.IntegerField(choices=TYPE_CHOICES_NORM, unique=True)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class AboutExpressions(models.Model):
    number = models.IntegerField(max_length=20, default=0)
    block_expression_num = models.IntegerField(max_length=50, default=0)
    user_expression = models.CharField(max_length=100, blank=False)
    user_ans = models.CharField(max_length=150, blank=False)
    true_ans = models.CharField(max_length=15, default='1')
    points_for_solve = models.IntegerField(default=1, blank=False)
    user_eps = models.CharField(max_length=150, default="0", blank=True)
    user_type = models.ForeignKey(TypeAnswer, on_delete=models.SET_NULL, null=True)
    exist_select = models.BooleanField(default=False)

    def __str__(self):
        return self.user_expression

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class TypeNormForMatrix(models.Model):
    num_expr = models.ForeignKey(AboutExpressions, on_delete=models.CASCADE)
    matrix_norms = models.ForeignKey(TypeNorm, on_delete=models.SET_NULL, null=True)


class TypeNormForTaskVariant(models.Model):
    task_variant = models.ForeignKey('TaskVariant', on_delete=models.CASCADE)
    matrix_norms = models.ForeignKey(TypeNorm, on_delete=models.SET_NULL, null=True)


class Subjects(models.Model):
    name = models.CharField(max_length=100, unique=True, default="Другое")

    def __str__(self):
        return self.name


class TaskGroup(models.Model):
    number = models.IntegerField(default=1)  # Номер группы заданий
    points_for_solve = models.IntegerField(default=1)  # Баллы за решение этой группы

    def __str__(self):
        return f"Группа заданий №{self.number}"


class TaskVariant(models.Model):
    task_group = models.ForeignKey(TaskGroup, on_delete=models.CASCADE, related_name='variants')
    user_expression = models.CharField(max_length=100, blank=False)
    user_ans = models.CharField(max_length=150, blank=False)
    true_ans = models.CharField(max_length=15, default='1')
    user_eps = models.CharField(max_length=150, default="0", blank=True)
    user_type = models.ForeignKey(TypeAnswer, on_delete=models.SET_NULL, null=True)
    exist_select = models.BooleanField(default=False)

    def __str__(self):
        return f"Вариант {self.id} группы {self.task_group.number}"


class AboutTest(models.Model):
    objects = None
    name_tests = models.CharField(max_length=255, blank=False)  # Название теста
    creator = models.ForeignKey(TeacherData, on_delete=models.PROTECT, null=True, blank=True,
                                related_name='created_tests')  # Создатель теста
    time_to_solution = models.DurationField(default=timedelta(hours=1, minutes=30))
    name_slug_tests = models.SlugField(max_length=255, unique=True, db_index=True, verbose_name="URL")  # Слаг имени
    num_of_attempts = models.IntegerField(blank=True, default=1)  # Количество попыток для решения
    type_of_result = models.IntegerField(blank=True, default=1)  # Тип возвращаемого результата
    description = models.CharField(max_length=150, default="", blank=True)
    is_published = models.IntegerField(default=0)
    is_done = models.IntegerField(default=1)
    is_draft = models.BooleanField(default=False)
    subj = models.ForeignKey(Subjects,
                             on_delete=models.PROTECT,
                             default=1)

    # publish_date = models.DateTimeField(auto_now_add=True)  # Дата публикации (можно будет отложить публикацию)
    # expiration_date = models.DateTimeField(null=True, blank=True)  # Время публикации (аналогично)
    # time_last_change = models.DateTimeField(auto_now=True)  # Время последнего изменения теста
    expressions = models.ManyToManyField(AboutExpressions)
    task_groups = models.ManyToManyField(TaskGroup, blank=True)  # Новые группы заданий

    def __str__(self):
        return self.name_tests

    def save(self, *args, **kwargs):
        if not self.id:  # Проверка на создание нового объекта
            base_slug = slugify(unidecode(self.name_tests))
            slug = base_slug
            counter = 1

            # Проверяем уникальность slug'а
            while AboutTest.objects.filter(name_slug_tests=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.name_slug_tests = slug
        super().save(*args, **kwargs)


class PublishedGroup(models.Model):
    group_name = ForeignKey(StudentGroup, on_delete=models.PROTECT)
    test_name = ForeignKey(AboutTest, on_delete=models.PROTECT)
    teacher_name = ForeignKey(TeacherData, on_delete=models.PROTECT)


@receiver(pre_delete, sender=AboutTest)
def delete_related_expressions(sender, instance, **kwargs):
    instance.expressions.clear()
