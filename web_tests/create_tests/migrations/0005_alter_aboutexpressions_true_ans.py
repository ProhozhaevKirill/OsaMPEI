# Generated by Django 5.0.6 on 2025-03-11 21:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('create_tests', '0004_alter_aboutexpressions_true_ans'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aboutexpressions',
            name='true_ans',
            field=models.CharField(default='1', max_length=15),
        ),
    ]
