from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('create_tests', '0036_alter_aboutexpressions_true_ans_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='abouttest',
            name='publish_from',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='abouttest',
            name='publish_until',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
