# Generated by Django 5.0.6 on 2025-05-17 19:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('solving_tests', '0002_studentresult_delete_after'),
    ]

    operations = [
        migrations.RenameField(
            model_name='studentresult',
            old_name='resAnswer',
            new_name='res_answer',
        ),
        migrations.RenameField(
            model_name='studentresult',
            old_name='resultPoints',
            new_name='result_points',
        ),
        migrations.RenameField(
            model_name='studentresult',
            old_name='teacherExpressions',
            new_name='teacher_expressions',
        ),
        migrations.RemoveField(
            model_name='studentresult',
            name='delete_after',
        ),
    ]
