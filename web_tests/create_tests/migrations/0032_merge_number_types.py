from django.db import migrations


def merge_number_types(apps, schema_editor):
    TypeAnswer = apps.get_model('create_tests', 'TypeAnswer')
    AboutExpressions = apps.get_model('create_tests', 'AboutExpressions')
    TaskVariant = apps.get_model('create_tests', 'TaskVariant')

    try:
        type_number = TypeAnswer.objects.get(type_code=1)
    except TypeAnswer.DoesNotExist:
        return

    try:
        type_float = TypeAnswer.objects.get(type_code=2)
        AboutExpressions.objects.filter(user_type=type_float).update(user_type=type_number)
        TaskVariant.objects.filter(user_type=type_float).update(user_type=type_number)
        type_float.delete()
    except TypeAnswer.DoesNotExist:
        pass

    type_number.name = 'Число'
    type_number.save()


class Migration(migrations.Migration):

    dependencies = [
        ('create_tests', '0031_add_free_answer_type'),
    ]

    operations = [
        migrations.RunPython(merge_number_types, migrations.RunPython.noop),
    ]
