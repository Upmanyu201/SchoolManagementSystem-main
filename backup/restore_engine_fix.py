# Fixed Restore Engine for School Management System
# backup\restore_engine.py
import json
import os
import logging
from typing import Dict, List, Any, Tuple, Optional
from django.apps import apps
from django.db import transaction, IntegrityError
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from datetime import datetime

# Configure detailed logging for restore engine
logger = logging.getLogger('backup.restore')

class SchoolDataRestoreEngine:
    """
    Intelligent restore engine that understands School Management System data structure
    """
    
    # Application data mapping matching ALLOWED_APPS
    ALLOWED_APPS = [
        "core", "school_profile", "teachers", "subjects", "students", 
        "transport", "student_fees", "fees", "fines", "attendance", 
        "promotion", "reports", "messaging", "users"
    ]
    
    APP_CATEGORIES = {
        'students': {
            'apps': ['students', 'student_fees', 'attendance', 'promotion'],
            'models': ['students.student', 'student_fees.feedeposit', 'attendance.attendance'],
            'description': 'Student records, fees, attendance and promotion data'
        },
        'staff': {
            'apps': ['teachers', 'subjects'],
            'models': ['teachers.teacher', 'subjects.subject'],
            'description': 'Teacher profiles and subject assignments'
        },
        'financial': {
            'apps': ['fees', 'student_fees', 'fines'],
            'models': ['fees.feesgroup', 'fees.feestype', 'student_fees.feedeposit', 'fines.fine', 'fines.finestudent'],
            'description': 'Fee structures, payments, and financial records'
        },
        'transport': {
            'apps': ['transport'],
            'models': ['transport.route', 'transport.stoppage', 'transport.transportassignment'],
            'description': 'Transport routes and student assignments'
        },
        'core': {
            'apps': ['core', 'school_profile'],
            'models': ['core.academicclass', 'core.section', 'school_profile.schoolprofile'],
            'description': 'Core system settings and school profile'
        },
        'system': {
            'apps': ['users', 'messaging', 'reports'],
            'models': ['users.customuser', 'messaging.message', 'reports.report'],
            'description': 'System users, messaging and reports'
        }
    }
    
    # Model dependency order for safe restoration
    MODEL_DEPENDENCY_ORDER = [
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
        'transport.transportassignment',
        'student_fees.feedeposit',
        'fines.fine',
        'fines.finestudent',
        'attendance.attendance',
    ]
    
    def __init__(self):
        logger.info("=== ENGINE INIT START ===")
        
        try:
            self.restore_stats = {
                'total_records': 0,
                'processed': 0,
                'created': 0,
                'updated': 0,
                'skipped': 0,
                'errors': 0,
                'categories': {}
            }
            
            # Test critical imports
            from django.apps import apps
            from django.db import transaction
            logger.info("ENGINE INIT: Django imports successful")
            
            logger.info("=== ENGINE INIT SUCCESS ===")
        except Exception as e:
            logger.error(f"=== ENGINE INIT FAILED ===: {e}", exc_info=True)
            raise
    
    def analyze_backup_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze backup file and determine data categories"""
        from .security_utils import safe_log_info
        safe_log_info(logger, "Starting backup file analysis: %s", file_path)
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Backup file not found: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                raise ValueError("Invalid backup format - expected JSON array")
            
            logger.info(f"Backup file loaded successfully, {len(data)} records found")
            
            analysis = {
                'total_records': len(data),
                'categories_found': {},
                'models_found': set(),
                'data_quality': 'good',
                'recommendations': []
            }
            
            # Group by model and analyze
            for item in data:
                if not isinstance(item, dict) or 'model' not in item:
                    continue
                    
                model_name = item['model'].lower()
                analysis['models_found'].add(model_name)
                
                # Categorize by app type
                for category, config in self.APP_CATEGORIES.items():
                    if model_name in config['models']:
                        if category not in analysis['categories_found']:
                            analysis['categories_found'][category] = {
                                'count': 0,
                                'models': []
                            }
                        analysis['categories_found'][category]['count'] += 1
                        if model_name not in analysis['categories_found'][category]['models']:
                            analysis['categories_found'][category]['models'].append(model_name)
            
            # Generate recommendations
            if 'students' in analysis['categories_found']:
                analysis['recommendations'].append("Student data found - ensure core classes/sections are restored first")
            if 'financial' in analysis['categories_found']:
                analysis['recommendations'].append("Financial data found - verify fee structures before student fees")
            if 'transport' in analysis['categories_found']:
                analysis['recommendations'].append("Transport data found - routes must be created before assignments")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Backup analysis failed for {file_path}: {e}", exc_info=True)
            raise ValueError(f"Cannot analyze backup file: {e}")
    
    def restore_full_backup(self, file_path: str, mode: str = 'merge') -> Dict[str, Any]:
        """Restore complete backup with intelligent dependency handling"""
        logger.info(f"=== FULL RESTORE START === file: {file_path}, mode: {mode}")
        
        try:
            # Analyze backup first
            analysis = self.analyze_backup_file(file_path)
            logger.info(f"Backup analysis: {analysis['total_records']} records, {len(analysis['categories_found'])} categories")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Group data by model
            grouped_data = self._group_by_model(data)
            
            with transaction.atomic():
                if mode == 'replace':
                    self._clear_existing_data(list(grouped_data.keys()))
                
                # Restore in dependency order
                for model_name in self.MODEL_DEPENDENCY_ORDER:
                    if model_name in grouped_data:
                        self._restore_model_data(model_name, grouped_data[model_name], mode)
                
                # Restore remaining models not in order
                for model_name, records in grouped_data.items():
                    if model_name not in self.MODEL_DEPENDENCY_ORDER:
                        self._restore_model_data(model_name, records, mode)
            
            self.restore_stats['analysis'] = analysis
            logger.info(f"Full restore completed: {self.restore_stats}")
            return self.restore_stats
            
        except Exception as e:
            logger.error(f"=== FULL RESTORE FAILED ===: {e}", exc_info=True)
            raise
    
    def restore_category_backup(self, file_path: str, category: str, mode: str = 'merge') -> Dict[str, Any]:
        """Restore specific data category (students, staff, financial, etc.)"""
        if category not in self.APP_CATEGORIES:
            raise ValueError(f"Unknown category: {category}")
        
        logger.info(f"Starting {category} category restore from {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Filter data for this category
            category_config = self.APP_CATEGORIES[category]
            filtered_data = []
            
            for item in data:
                if isinstance(item, dict) and 'model' in item:
                    model_name = item['model'].lower()
                    if model_name in category_config['models']:
                        filtered_data.append(item)
            
            if not filtered_data:
                logger.warning(f"No {category} data found in backup")
                return {'message': f'No {category} data found in backup file'}
            
            # Group and restore
            grouped_data = self._group_by_model(filtered_data)
            
            with transaction.atomic():
                if mode == 'replace':
                    self._clear_category_data(category)
                
                # Restore in dependency order
                for model_name in self.MODEL_DEPENDENCY_ORDER:
                    if model_name in grouped_data:
                        self._restore_model_data(model_name, grouped_data[model_name], mode)
            
            logger.info(f"Category {category} restore completed: {self.restore_stats}")
            return self.restore_stats
            
        except Exception as e:
            logger.error(f"Category restore failed: {e}")
            raise
    
    def _group_by_model(self, data: List[Dict]) -> Dict[str, List[Dict]]:
        """Group backup records by model"""
        grouped = {}
        for item in data:
            if isinstance(item, dict) and 'model' in item:
                model_name = item['model'].lower()
                if model_name not in grouped:
                    grouped[model_name] = []
                grouped[model_name].append(item)
        return grouped
    
    def _restore_model_data(self, model_name: str, records: List[Dict], mode: str):
        """Restore data for a specific model"""
        logger.info(f"Starting restore for model {model_name} with {len(records)} records")
        try:
            if '.' not in model_name:
                logger.error(f"Invalid model name format: {model_name}")
                return
                
            app_label, model_class = model_name.split('.', 1)
            
            # Check if app is allowed
            if app_label not in self.ALLOWED_APPS:
                logger.warning(f"Skipping {model_name} - app '{app_label}' not in ALLOWED_APPS")
                return
            
            try:
                model = apps.get_model(app_label, model_class)
            except Exception as e:
                logger.error(f"Cannot get model {model_name}: {e}")
                return
            
            category = self._get_model_category(model_name)
            if category not in self.restore_stats['categories']:
                self.restore_stats['categories'][category] = {
                    'created': 0, 'updated': 0, 'skipped': 0, 'errors': 0
                }
            
            logger.info(f"Restoring {len(records)} records for {model_name} in category {category}")
            
            for i, record in enumerate(records):
                try:
                    self._restore_single_record(model, record, mode, category)
                    self.restore_stats['processed'] += 1
                    if (i + 1) % 100 == 0:
                        logger.info(f"Processed {i + 1}/{len(records)} records for {model_name}")
                except Exception as e:
                    logger.error(f"Failed to restore {model_name} record {i}: {e}")
                    self.restore_stats['errors'] += 1
                    self.restore_stats['categories'][category]['errors'] += 1
            
            logger.info(f"Completed restore for {model_name}: {len(records)} records processed")
            
        except Exception as e:
            logger.error(f"Model {model_name} restore failed: {e}", exc_info=True)
            raise
    
    def _restore_single_record(self, model, record: Dict, mode: str, category: str):
        """Restore a single database record with comprehensive error handling"""
        try:
            fields = record.get('fields', {})
            pk = record.get('pk')
            
            if not fields:
                logger.warning(f"Empty fields for {model._meta.label} pk={pk}")
                self.restore_stats['skipped'] += 1
                self.restore_stats['categories'][category]['skipped'] += 1
                return
            
            # Clean and validate fields
            try:
                cleaned_fields = self._clean_model_fields(model, fields)
            except Exception as clean_error:
                logger.error(f"Field cleaning failed for {model._meta.label} pk={pk}: {clean_error}")
                self.restore_stats['errors'] += 1
                self.restore_stats['categories'][category]['errors'] += 1
                return
            
            # Check for existing record
            existing = None
            if pk:
                try:
                    existing = model.objects.get(pk=pk)
                except model.DoesNotExist:
                    pass
                except Exception as lookup_error:
                    logger.error(f"Error looking up existing record {model._meta.label} pk={pk}: {lookup_error}")
            
            if existing:
                if mode == 'merge':
                    try:
                        # Update existing record
                        for field_name, value in cleaned_fields.items():
                            if hasattr(existing, field_name):
                                setattr(existing, field_name, value)
                        existing.save()
                        self.restore_stats['updated'] += 1
                        self.restore_stats['categories'][category]['updated'] += 1
                        logger.debug(f"Updated {model._meta.label} pk={pk}")
                    except Exception as update_error:
                        logger.error(f"Failed to update {model._meta.label} pk={pk}: {update_error}")
                        self.restore_stats['errors'] += 1
                        self.restore_stats['categories'][category]['errors'] += 1
                else:
                    # Skip in replace mode (already cleared)
                    self.restore_stats['skipped'] += 1
                    self.restore_stats['categories'][category]['skipped'] += 1
            else:
                try:
                    # Create new record
                    if pk and 'id' not in cleaned_fields:
                        cleaned_fields['id'] = pk
                    
                    new_obj = model.objects.create(**cleaned_fields)
                    self.restore_stats['created'] += 1
                    self.restore_stats['categories'][category]['created'] += 1
                    logger.debug(f"Created {model._meta.label} pk={new_obj.pk}")
                except IntegrityError as integrity_error:
                    logger.warning(f"Integrity constraint for {model._meta.label}: {integrity_error}")
                    self.restore_stats['skipped'] += 1
                    self.restore_stats['categories'][category]['skipped'] += 1
                except Exception as create_error:
                    logger.error(f"Failed to create {model._meta.label}: {create_error}")
                    self.restore_stats['errors'] += 1
                    self.restore_stats['categories'][category]['errors'] += 1
        
        except Exception as record_error:
            logger.error(f"Unexpected error restoring record for {model._meta.label}: {record_error}")
            self.restore_stats['errors'] += 1
            if category in self.restore_stats['categories']:
                self.restore_stats['categories'][category]['errors'] += 1
    
    def _clean_model_fields(self, model, fields: Dict) -> Dict:
        """Clean and validate fields for model with enhanced error handling"""
        cleaned = {}
        model_label = getattr(model._meta, 'label', str(model))
        
        try:
            # Get valid field names, excluding reverse relations
            valid_fields = set()
            try:
                for f in model._meta.get_fields():
                    if hasattr(f, 'name') and not f.many_to_many and not (hasattr(f, 'related_model') and f.related_model):
                        valid_fields.add(f.name)
            except Exception as e:
                logger.error(f"Error getting model fields for {model_label}: {e}")
                raise
            
            # Also include common field names that might be valid
            for field_name in fields.keys():
                try:
                    model._meta.get_field(field_name)
                    valid_fields.add(field_name)
                except:
                    pass
            
            for field_name, value in fields.items():
                if field_name in valid_fields:
                    try:
                        field = model._meta.get_field(field_name)
                        cleaned_value = self._convert_field_value(field, value)
                        cleaned[field_name] = cleaned_value
                    except Exception as e:
                        logger.warning(f"Field conversion failed for {model_label}.{field_name}: {e}")
                        # Skip problematic fields rather than including raw value
                        continue
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Field cleaning failed for {model_label}: {e}", exc_info=True)
            raise ValueError(f"Cannot clean fields for {model_label}: {e}")
    
    def _convert_field_value(self, field, value):
        """Convert field value to appropriate type with comprehensive error handling"""
        if value in ('', 'null', 'None', None):
            return None
        
        from django.db import models
        
        try:
            field_name = getattr(field, 'name', 'unknown')
            
            if isinstance(field, models.DecimalField):
                if value is None or value == '':
                    return None
                try:
                    return Decimal(str(value))
                except (ValueError, TypeError) as e:
                    logger.warning(f"Cannot convert '{value}' to Decimal for field {field_name}: {e}")
                    return None
                    
            elif isinstance(field, models.BooleanField):
                if isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes', 'on')
                return bool(value)
                
            elif isinstance(field, (models.IntegerField, models.AutoField, models.BigIntegerField)):
                if value is None or value == '':
                    return None
                try:
                    return int(float(value))  # Handle decimal strings
                except (ValueError, TypeError) as e:
                    logger.warning(f"Cannot convert '{value}' to int for field {field_name}: {e}")
                    return None
                    
            elif isinstance(field, models.FloatField):
                if value is None or value == '':
                    return None
                try:
                    return float(value)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Cannot convert '{value}' to float for field {field_name}: {e}")
                    return None
                    
            elif isinstance(field, models.DateTimeField):
                if isinstance(value, str) and value:
                    try:
                        # Handle various datetime formats
                        if 'T' in value:
                            return datetime.fromisoformat(value.replace('Z', '+00:00'))
                        else:
                            return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                    except ValueError as e:
                        logger.warning(f"Could not parse datetime '{value}' for field {field_name}: {e}")
                        return None
                return value
                
            elif isinstance(field, models.DateField):
                if isinstance(value, str) and value:
                    try:
                        return datetime.strptime(value, '%Y-%m-%d').date()
                    except ValueError as e:
                        logger.warning(f"Could not parse date '{value}' for field {field_name}: {e}")
                        return None
                return value
                
            elif isinstance(field, models.CharField):
                if value is None:
                    return None
                str_value = str(value)
                if hasattr(field, 'max_length') and field.max_length and len(str_value) > field.max_length:
                    logger.warning(f"Truncating CharField value for {field_name}: {len(str_value)} > {field.max_length}")
                    return str_value[:field.max_length]
                return str_value
                
            elif isinstance(field, models.TextField):
                return str(value) if value is not None else None
            
            # Default: return as-is
            return value
            
        except (ValueError, TypeError, OverflowError) as e:
            logger.warning(f"Field conversion error for {getattr(field, 'name', 'unknown')}: {e}, using None")
            return None
        except Exception as e:
            logger.error(f"Unexpected conversion error for {getattr(field, 'name', 'unknown')}: {e}")
            return None  # Return None instead of raising to prevent crashes
    
    def _get_model_category(self, model_name: str) -> str:
        """Get category for a model"""
        for category, config in self.APP_CATEGORIES.items():
            if model_name in config['models']:
                return category
        return 'other'
    
    def _clear_existing_data(self, model_names: List[str]):
        """Clear existing data for replace mode"""
        logger.warning("Clearing existing data for replace mode")
        
        # Clear in reverse dependency order
        for model_name in reversed(self.MODEL_DEPENDENCY_ORDER):
            if model_name in model_names:
                try:
                    app_label, model_class = model_name.split('.')
                    
                    # Skip if app not allowed
                    if app_label not in self.ALLOWED_APPS:
                        continue
                    
                    model = apps.get_model(app_label, model_class)
                    count = model.objects.count()
                    if count > 0:
                        model.objects.all().delete()
                        logger.info(f"Cleared {count} records from {model_name}")
                except Exception as e:
                    logger.error(f"Failed to clear {model_name}: {e}")
    
    def _clear_category_data(self, category: str):
        """Clear data for specific category"""
        category_config = self.APP_CATEGORIES[category]
        logger.warning(f"Clearing existing {category} data")
        
        for model_name in reversed(category_config['models']):
            try:
                app_label, model_class = model_name.split('.')
                model = apps.get_model(app_label, model_class)
                count = model.objects.count()
                if count > 0:
                    model.objects.all().delete()
                    logger.info(f"Cleared {count} records from {model_name}")
            except Exception as e:
                logger.error(f"Failed to clear {model_name}: {e}")
    
    def get_restore_summary(self) -> Dict[str, Any]:
        """Get detailed restore summary"""
        return {
            'total_processed': self.restore_stats['processed'],
            'created': self.restore_stats['created'],
            'updated': self.restore_stats['updated'],
            'skipped': self.restore_stats['skipped'],
            'errors': self.restore_stats['errors'],
            'categories': self.restore_stats['categories'],
            'success_rate': (self.restore_stats['processed'] - self.restore_stats['errors']) / max(1, self.restore_stats['processed']) * 100
        }