from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, role=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email).lower()  # Приводим к нижнему регистру
        user = self.model(email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, role='admin', **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    THEME_CHOICES = [
        ('light', 'Светлая'),
        ('dark', 'Тёмная'),
    ]

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=[('student', 'Student'), ('teacher', 'Teacher')])
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='light')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['role']

    def save(self, *args, **kwargs):
        # Приводим email к нижнему регистру при сохранении
        if self.email:
            self.email = self.email.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email

    def get_full_name(self):
        if self.role == 'student' and hasattr(self, 'studentdata'):
            return f"{self.studentdata.last_name} {self.studentdata.first_name}"
        elif self.role == 'teacher' and hasattr(self, 'teacherdata'):
            return f"{self.teacherdata.last_name} {self.teacherdata.first_name}"
        return self.email

    def get_photo_url(self):
        if self.role == 'student' and hasattr(self, 'studentdata') and self.studentdata.photo:
            return self.studentdata.photo.url
        elif self.role == 'teacher' and hasattr(self, 'teacherdata') and self.teacherdata.photo:
            return self.teacherdata.photo.url
        return None


# class Subject(models.Model):
#     name_subj = models.CharField(max_length=100, default="Другое")
#
#     def __str__(self):
#         return self.name_subj


class StudentInstitute(models.Model):
    name = models.CharField(max_length=70, unique=True)

    def __str__(self):
        return self.name


class StudentGroup(models.Model):
    EDUCATION_LEVEL_CHOICES = [
        ('bachelor', 'Бакалавриат'),
        ('master', 'Магистратура'),
    ]

    COURSE_CHOICES = [
        (1, '1 курс'),
        (2, '2 курс'),
        (3, '3 курс'),
        (4, '4 курс'),
    ]

    name = models.CharField(max_length=20, unique=True)
    name_inst = models.ForeignKey(StudentInstitute, on_delete=models.PROTECT)
    education_level = models.CharField(max_length=8, choices=EDUCATION_LEVEL_CHOICES, default='bachelor')
    course = models.IntegerField(choices=COURSE_CHOICES, default=1)

    def __str__(self):
        return self.name


class StudentData(models.Model):
    first_name = models.CharField(max_length=50, blank=False)
    last_name = models.CharField(max_length=50, blank=False)
    middle_name = models.CharField(max_length=50, blank=True)
    photo = models.ImageField(upload_to='user_photos/', blank=True, null=True)

    training_status = models.BooleanField(default=True)
    count_solve = models.IntegerField(default=0)
    perc_of_correct_ans = models.CharField(max_length=5, default="0")

    institute = models.ForeignKey(StudentInstitute, on_delete=models.PROTECT)
    # direction = models.ForeignKey(StudentDirection, on_delete=models.PROTECT)
    # department = models.ForeignKey(StudentDepartment, on_delete=models.PROTECT)
    group = models.ForeignKey(StudentGroup, on_delete=models.PROTECT)
    data_map = models.OneToOneField(CustomUser, on_delete=models.CASCADE)


class WhiteList(models.Model):
    teacher_mail = models.EmailField(unique=True)

    def __str__(self):
        return self.teacher_mail


class TeacherData(models.Model):
    first_name = models.CharField(max_length=50, blank=False)
    last_name = models.CharField(max_length=50, blank=False)
    middle_name = models.CharField(max_length=50)
    photo = models.ImageField(upload_to='user_photos/', blank=True, null=True)
    institute = models.ForeignKey(StudentInstitute, default=6, on_delete=models.PROTECT)

    data_map = models.OneToOneField(CustomUser, on_delete=models.CASCADE)

