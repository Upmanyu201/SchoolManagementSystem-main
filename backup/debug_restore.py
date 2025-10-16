#!/usr/bin/env python3
"""
Debug script to check backup file contents and restore issues
"""

import os
import json
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_management.settings')
django.setup()

def debug_backup_file(backup_id):
    """Debug a specific backup file"""
    from backup.models import BackupHistory
    from django.conf import settings
    
    try:
        backup = BackupHistory.objects.get(id=backup_id)
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        backup_path = os.path.join(backup_dir, backup.file_name)
        
        print(f"=== BACKUP DEBUG INFO ===")
        print(f"Backup ID: {backup_id}")
        print(f"File name: {backup.file_name}")
        print(f"File path: {backup_path}")
        print(f"File exists: {os.path.exists(backup_path)}")
        
        if os.path.exists(backup_path):
            file_size = os.path.getsize(backup_path)
            print(f"File size: {file_size} bytes")
            
            if file_size > 0:
                with open(backup_path, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                        print(f"JSON valid: Yes")
                        print(f"Total records: {len(data)}")
                        
                        # Group by model
                        models = {}
                        for item in data:
                            if isinstance(item, dict) and 'model' in item:
                                model_name = item['model']
                                models[model_name] = models.get(model_name, 0) + 1
                        
                        print(f"Models found:")
                        for model, count in sorted(models.items()):
                            print(f"  {model}: {count} records")
                            
                        # Show sample record
                        if data:
                            print(f"\nSample record:")
                            sample = data[0]
                            print(f"  Model: {sample.get('model')}")
                            print(f"  PK: {sample.get('pk')}")
                            print(f"  Fields: {list(sample.get('fields', {}).keys())}")
                            
                    except json.JSONDecodeError as e:
                        print(f"JSON invalid: {e}")
            else:
                print("File is empty!")
        else:
            print("File does not exist!")
            
    except Exception as e:
        print(f"Error: {e}")

def test_restore_process(backup_id):
    """Test the restore process step by step"""
    from backup.views import safe_merge_restore
    from backup.models import BackupHistory
    from django.conf import settings
    
    try:
        backup = BackupHistory.objects.get(id=backup_id)
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        backup_path = os.path.join(backup_dir, backup.file_name)
        
        print(f"\n=== TESTING RESTORE PROCESS ===")
        print(f"Backup file: {backup_path}")
        
        if not os.path.exists(backup_path):
            print("ERROR: Backup file does not exist!")
            return
            
        # Test the restore function
        result = safe_merge_restore(backup_path)
        print(f"Restore result: {result}")
        
    except Exception as e:
        print(f"Restore test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python debug_restore.py <backup_id>")
        sys.exit(1)
    
    backup_id = int(sys.argv[1])
    debug_backup_file(backup_id)
    
    # Ask if user wants to test restore
    response = input("\nDo you want to test the restore process? (y/N): ")
    if response.lower() == 'y':
        test_restore_process(backup_id)