from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('solving_tests', '0007_final_fix_max_points'),
    ]

    operations = [
        migrations.CreateModel(
            name='FreeAnswerGrade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_index', models.IntegerField()),
                ('is_correct', models.BooleanField(null=True, blank=True)),
                ('student_result', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='free_answer_grades',
                    to='solving_tests.studentresult',
                )),
            ],
            options={
                'unique_together': {('student_result', 'question_index')},
            },
        ),
    ]
