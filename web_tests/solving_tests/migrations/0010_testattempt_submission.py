from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('solving_tests', '0009_alter_studentresult_res_answer_testattempt_and_more')]
    operations = [
        migrations.AddField(model_name='testattempt', name='submitted_at', field=models.DateTimeField(null=True, blank=True, db_index=True)),
        migrations.AddField(model_name='testattempt', name='grading_details', field=models.JSONField(null=True, blank=True)),
    ]
