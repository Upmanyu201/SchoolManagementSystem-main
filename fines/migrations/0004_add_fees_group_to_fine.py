# fines/migrations/0004_add_fees_group_to_fine.py

import django.db.models.deletion
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('fees', '0001_initial'), # Dependency needed for the ForeignKey
        ('fines', '0003_add_is_waived'), # Last applied migration
    ]

    operations = [
        # Explicitly add the missing fees_group ForeignKey field
        migrations.AddField(
            model_name='fine',
            name='fees_group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='fees.feesgroup'),
        ),
    ]