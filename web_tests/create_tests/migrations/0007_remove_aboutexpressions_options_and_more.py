# Generated by Django 5.0.6 on 2025-03-12 06:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('create_tests', '0006_aboutexpressions_options'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='aboutexpressions',
            name='options',
        ),
        migrations.AddField(
            model_name='aboutexpressions',
            name='exist_select',
            field=models.BooleanField(default=False),
        ),
    ]
