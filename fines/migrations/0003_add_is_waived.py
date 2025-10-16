# fines/migrations/0003_add_is_waived.py

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('fines', '0002_initial'),
    ]

    operations = [
        # Explicitly add the missing column
        migrations.AddField(
            model_name='finestudent',
            name='is_waived',
            field=models.BooleanField(default=False),
        ),
    ]