from django.db import migrations, models


def rename_symbolic_type(apps, schema_editor):
    TypeAnswer = apps.get_model('create_tests', 'TypeAnswer')
    TypeAnswer.objects.filter(type_code=3).update(name='Символьные выражения')


def restore_old_name(apps, schema_editor):
    TypeAnswer = apps.get_model('create_tests', 'TypeAnswer')
    TypeAnswer.objects.filter(type_code=3).update(name='Строки')


class Migration(migrations.Migration):

    dependencies = [
        ('create_tests', '0037_abouttest_publication_window'),
    ]

    operations = [
        migrations.AlterField(
            model_name='typeanswer',
            name='type_code',
            field=models.IntegerField(
                choices=[
                    (1, 'Число'),
                    (3, 'Символьные выражения'),
                    (4, 'Матрицы'),
                    (5, 'Свободный ответ'),
                ],
                unique=True,
            ),
        ),
        migrations.RunPython(rename_symbolic_type, restore_old_name),
    ]
