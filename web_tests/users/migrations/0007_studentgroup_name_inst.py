# Generated by Django 5.0.6 on 2025-04-24 10:53

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_remove_studentdata_department_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentgroup',
            name='name_inst',
            field=models.ForeignKey(default=6, on_delete=django.db.models.deletion.PROTECT, to='users.studentinstitute'),
        ),
    ]
