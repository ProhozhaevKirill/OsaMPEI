from django.db import migrations, models


def add_free_answer_type(apps, schema_editor):
    TypeAnswer = apps.get_model('create_tests', 'TypeAnswer')
    TypeAnswer.objects.get_or_create(type_code=5, defaults={'name': 'Свободный ответ'})


def remove_free_answer_type(apps, schema_editor):
    TypeAnswer = apps.get_model('create_tests', 'TypeAnswer')
    TypeAnswer.objects.filter(type_code=5).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('create_tests', '0030_abouttest_draft_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='typeanswer',
            name='type_code',
            field=models.IntegerField(
                choices=[
                    (1, 'Целые'),
                    (2, 'Нецелые'),
                    (3, 'Строки'),
                    (4, 'Матрицы'),
                    (5, 'Свободный ответ'),
                ],
                unique=True,
            ),
        ),
        migrations.RunPython(add_free_answer_type, remove_free_answer_type),
    ]
