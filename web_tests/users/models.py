from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, role=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, role='admin', **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=[('student', 'Student'), ('teacher', 'Teacher')])
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['role']

    def __str__(self):
        return self.email


# class Subject(models.Model):
#     name_subj = models.CharField(max_length=100, default="Другое")
#
#     def __str__(self):
#         return self.name_subj


class StudentInstitute(models.Model):
    name = models.CharField(max_length=70, unique=True)

    def __str__(self):
        return self.name


# class StudentDirection(models.Model):
#     name = models.CharField(max_length=256, unique=True)
#
#     def __str__(self):
#         return self.name
#
#
# class StudentDepartment(models.Model):
#     name = models.CharField(max_length=256, unique=True)
#
#     def __str__(self):
#         return self.name


class StudentGroup(models.Model):
    name = models.CharField(max_length=20, unique=True)
    name_inst = models.ForeignKey(StudentInstitute, on_delete=models.PROTECT)

    def __str__(self):
        return self.name


class StudentData(models.Model):
    first_name = models.CharField(max_length=50, blank=False)
    last_name = models.CharField(max_length=50, blank=False)
    middle_name = models.CharField(max_length=50, blank=True)

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
        return self.teacherMail


class TeacherData(models.Model):
    first_name = models.CharField(max_length=50, blank=False)
    last_name = models.CharField(max_length=50, blank=False)
    middle_name = models.CharField(max_length=50)

    data_map = models.OneToOneField(CustomUser, on_delete=models.CASCADE)

