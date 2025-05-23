# Generated by Django 5.0.6 on 2025-05-15 12:00

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('create_tests', '0012_aboutexpressions_user_type'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attempt_number', models.PositiveIntegerField(default=1)),
                ('resultPoints', models.FloatField()),
                ('resAnswer', models.CharField(blank=True, max_length=255)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('teacherExpressions', models.ManyToManyField(to='create_tests.aboutexpressions')),
                ('test', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='create_tests.abouttest')),
            ],
            options={
                'unique_together': {('student', 'test', 'attempt_number')},
            },
        ),
    ]
