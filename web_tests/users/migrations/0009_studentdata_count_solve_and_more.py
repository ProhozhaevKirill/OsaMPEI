# Generated by Django 5.0.6 on 2025-05-03 12:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_alter_studentgroup_name_inst'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentdata',
            name='count_solve',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='studentdata',
            name='perc_of_correct_ans',
            field=models.CharField(default='0', max_length=5),
        ),
    ]
