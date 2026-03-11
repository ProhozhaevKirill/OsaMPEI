from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('create_tests', '0029_alter_aboutexpressions_block_expression_num_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='abouttest',
            name='draft_data',
            field=models.TextField(blank=True, default=''),
        ),
    ]
