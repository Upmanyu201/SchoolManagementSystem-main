"""Enhanced error recovery and rollback system"""
import os
import json
import shutil
import tempfile
from contextlib import contextmanager
from django.db import transaction
from django.core.management import call_command
from django.conf import settings
from django.utils import timezone
from .models import BackupJob, RestoreJob
import logging

logger = logging.getLogger('backup.recovery')

# Define ALLOWED_APPS for recovery operations
ALLOWED_APPS = [
    "core",
    "school_profile", 
    "teachers",
    "subjects",
    "students",
    "transport",
    "student_fees",
    "fees",
    "fines",
    "attendance",
    "promotion",
    "reports",
    'messaging',
    'users',
]

def clear_apps_data(app_list):
    """DEPRECATED: Clear data from specified apps while preserving critical system data
    
    WARNING: This function deletes ALL data from specified apps.
    Use safe_merge_restore() instead to avoid data loss.
    """
    from django.apps import apps
    
    logger.warning("clear_apps_data called - this will delete all existing data!")
    
    preserve_models = ['users.customuser', 'auth.user', 'auth.group', 'auth.permission']
    
    for app_label in app_list:
        if app_label == 'users':  # Skip users app to preserve accounts
            continue
            
        try:
            app_config = apps.get_app_config(app_label)
            for model in reversed(list(app_config.get_models())):
                model_label = f"{model._meta.app_label}.{model._meta.model_name}"
                if model_label.lower() not in preserve_models:
                    count = model.objects.count()
                    if count > 0:
                        logger.warning(f"Deleting {count} records from {model_label}")
                        model.objects.all().delete()
        except Exception as e:
            logger.warning(f"Could not clear data for app {app_label}: {e}")

def safe_merge_restore(json_file_path):
    """Safely restore data using merge strategy instead of clearing all data"""
    from django.apps import apps
    from django.db import IntegrityError
    from decimal import Decimal
    import logging
    
    logger = logging.getLogger('backup.restore')
    logger.info(f"Starting safe merge restore from: {json_file_path}")
    
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logger.info(f"Loaded {len(data)} records from backup file")
    
    if not isinstance(data, list):
        raise ValueError("Invalid backup format. Expected JSON array")
    
    # Group data by model
    model_data = {}
    for item in data:
        if not isinstance(item, dict) or 'model' not in item:
            continue
            
        model_name = item['model'].lower()
        if model_name not in model_data:
            model_data[model_name] = []
        
        try:
            app_label, model_class = item['model'].split('.')
            if app_label in ALLOWED_APPS:
                model = apps.get_model(app_label, model_class)
                valid_fields = {f.name for f in model._meta.get_fields()}
                
                # Clean fields to only include valid ones
                cleaned_fields = {k: v for k, v in item.get('fields', {}).items() if k in valid_fields}
                
                # Handle special cases for data type conversion
                for field_name, value in cleaned_fields.items():
                    try:
                        field = model._meta.get_field(field_name)
                        if hasattr(field, 'decimal_places') and isinstance(value, str):
                            cleaned_fields[field_name] = Decimal(value)
                    except:
                        pass
                
                item['fields'] = cleaned_fields
                model_data[model_name].append(item)
        except Exception as e:
            logger.warning(f"Skipping invalid model data: {e}")
            continue
    
    # Define model loading order to handle dependencies
    model_order = [
        'subjects.classsection',  # Load ClassSection first
        'core.academicclass',
        'core.section',
        'school_profile.schoolprofile',
        'teachers.teacher',
        'subjects.subject',
        'students.student',
        'transport.route',
        'transport.stoppage',
        'fees.feesgroup',
        'fees.feestype',
        'fines.finetype',
        'fines.fine',
        'transport.transportassignment',
        'student_fees.feedeposit',
        'fines.finestudent',
        'attendance.attendance',
    ]
    
    restored_count = 0
    skipped_count = 0
    
    # Process models in dependency order
    for model_name in model_order:
        if model_name in model_data and model_data[model_name]:
            try:
                model = apps.get_model(*model_name.split('.'))
                
                for item in model_data[model_name]:
                    try:
                        fields = item.get('fields', {})
                        pk = item.get('pk')
                        
                        # Try to find existing record
                        existing = None
                        if pk:
                            try:
                                existing = model.objects.get(pk=pk)
                            except model.DoesNotExist:
                                pass
                        
                        if existing:
                            # Update existing record
                            for field_name, value in fields.items():
                                setattr(existing, field_name, value)
                            existing.save()
                            logger.debug(f"Updated {model_name} record with pk={pk}")
                        else:
                            # Create new record
                            if pk:
                                fields['id'] = pk
                            model.objects.create(**fields)
                            logger.debug(f"Created new {model_name} record")
                        
                        restored_count += 1
                        
                    except IntegrityError as e:
                        logger.warning(f"Integrity error for {model_name}: {e}")
                        skipped_count += 1
                        continue
                    except Exception as e:
                        logger.warning(f"Error restoring {model_name} record: {e}")
                        skipped_count += 1
                        continue
                        
                logger.info(f"Processed {len(model_data[model_name])} records for {model_name}")
                
            except Exception as e:
                logger.error(f"Error processing model {model_name}: {e}")
                continue
    
    # Process remaining models not in order
    for model_name, items in model_data.items():
        if model_name not in model_order and items:
            try:
                model = apps.get_model(*model_name.split('.'))
                
                for item in items:
                    try:
                        fields = item.get('fields', {})
                        pk = item.get('pk')
                        
                        # Try to find existing record
                        existing = None
                        if pk:
                            try:
                                existing = model.objects.get(pk=pk)
                            except model.DoesNotExist:
                                pass
                        
                        if existing:
                            # Update existing record
                            for field_name, value in fields.items():
                                setattr(existing, field_name, value)
                            existing.save()
                        else:
                            # Create new record
                            if pk:
                                fields['id'] = pk
                            model.objects.create(**fields)
                        
                        restored_count += 1
                        
                    except IntegrityError as e:
                        logger.warning(f"Integrity error for {model_name}: {e}")
                        skipped_count += 1
                        continue
                    except Exception as e:
                        logger.warning(f"Error restoring {model_name} record: {e}")
                        skipped_count += 1
                        continue
                        
                logger.info(f"Processed {len(items)} records for {model_name}")
                
            except Exception as e:
                logger.error(f"Error processing model {model_name}: {e}")
                continue
    
    logger.info(f"Safe merge restore completed: {restored_count} restored, {skipped_count} skipped, {'error_count'} errors")
    
    # Print summary to console for debugging
    print(f"\n=== RESTORE SUMMARY ===")
    print(f"Total records processed: {len(data)}")
    print(f"Successfully restored: {restored_count}")
    print(f"Skipped (duplicates/integrity): {skipped_count}")
    print(f"Errors: {'error_count'}")
    print(f"Models processed: {list(model_data.keys())}")
    print(f"======================\n")
    
    return {'restored': restored_count, 'skipped': skipped_count, 'errors': 'error_count'}

def clean_and_restore_data(json_file_path):
    """DEPRECATED: Use safe_merge_restore() instead to avoid data loss"""
    logger.warning("clean_and_restore_data is deprecated. Use safe_merge_restore() instead.")
    return safe_merge_restore(json_file_path)

class RestoreRecoveryManager:
    """Manages restore operations with rollback capabilities"""
    
    @staticmethod
    def create_pre_restore_snapshot():
        """Create snapshot before restore for rollback"""
        try:
            snapshot_dir = os.path.join(settings.BASE_DIR, 'backups', 'snapshots')
            os.makedirs(snapshot_dir, exist_ok=True)
            
            from django.utils._os import safe_join
            snapshot_filename = f'pre_restore_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json'
            snapshot_file = safe_join(snapshot_dir, snapshot_filename)
            
            with open(snapshot_file, 'w', encoding='utf-8') as f:
                call_command('dumpdata', *ALLOWED_APPS, format='json', indent=2, stdout=f)
            
            logger.info(f"Pre-restore snapshot created: {snapshot_file}")
            return snapshot_file
            
        except Exception as e:
            logger.error(f"Failed to create snapshot: {e}")
            return None
    
    @staticmethod
    def rollback_from_snapshot(snapshot_file):
        """Rollback to pre-restore state"""
        try:
            if not os.path.exists(snapshot_file):
                raise FileNotFoundError(f"Snapshot file not found: {snapshot_file}")
            
            with transaction.atomic():
                # Clear current data
                clear_apps_data(ALLOWED_APPS)
                
                # Restore from snapshot
                clean_and_restore_data(snapshot_file)
            
            logger.info(f"Successfully rolled back from snapshot: {snapshot_file}")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False

@contextmanager
def safe_restore_operation(create_snapshot=True):
    """Context manager for safe restore operations with enhanced rollback"""
    from .context_managers import enhanced_restore_operation
    
    with enhanced_restore_operation(create_snapshot=create_snapshot) as context:
        yield context.get('snapshot_file')