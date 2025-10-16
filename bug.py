from fines.models import Fine
from fees.models import FeesGroup
from django.db import connection

print("Attempting to fix invalid foreign key data...")

# 1. Temporarily disable foreign key checks (specific to SQLite)
with connection.cursor() as cursor:
    cursor.execute('PRAGMA foreign_keys = OFF;')

try:
    # 2. Find and delete Fine objects with missing FeesGroup
    # We use raw SQL or a filtered delete since Django's ORM struggles with invalid FKs
    
    # Get all existing FeesGroup IDs
    valid_fees_group_ids = list(FeesGroup.objects.values_list('id', flat=True))
    
    # Use a raw query to identify and delete invalid rows
    with connection.cursor() as cursor:
        # Note: You need to know the exact field name which is 'fees_group_id'
        # The query finds IDs in fines_fine that are NOT in fees_feesgroup
        delete_query = f"""
        DELETE FROM fines_fine 
        WHERE fees_group_id IS NOT NULL 
          AND fees_group_id NOT IN ({', '.join(map(str, valid_fees_group_ids)) if valid_fees_group_ids else 'NULL'});
        """
        if not valid_fees_group_ids:
             # If there are no valid fees groups, delete all non-NULL fees_group_ids
             delete_query = "DELETE FROM fines_fine WHERE fees_group_id IS NOT NULL;"

        cursor.execute(delete_query)
        rows_deleted = cursor.rowcount
        print(f"Successfully deleted {rows_deleted} Fine record(s) with invalid fees_group_id.")
        
finally:
    # 3. Re-enable foreign key checks
    with connection.cursor() as cursor:
        cursor.execute('PRAGMA foreign_keys = ON;')

# 4. Exit the shell
exit()