# fines/migrations/0005_add_delay_days_to_fine.py

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        # Set dependency to the last successful migration (e.g., 0004)
        ('fines', '0004_add_fees_group_to_fine'), 
    ]

    operations = [
        # Explicitly add the missing column to the Fine model
        migrations.AddField(
            model_name='fine',
            name='delay_days',
            field=models.IntegerField(default=0),
            # Note: For production databases, you might need to set 'preserve_default=False' 
            # or specify 'default=0' for the field to be applied correctly.
        ),
    ]