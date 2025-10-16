# backup/services/export/csv_exporter.py
"""CSV export functionality"""

import csv
import logging
import time
from datetime import datetime
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied, ValidationError

from .base import DataExportService
from .constants import ExportConstants
from .row_formatters import RowFormatter

export_logger = logging.getLogger('export.api')

class CSVExporter(DataExportService):
    """CSV export service"""
    
    @classmethod
    def export_to_csv(cls, module_name, user):
        """Export module data to CSV format with enhanced security"""
        start_time = time.time()
        
        try:
            cls._validate_user_permissions(user, module_name)
            
            data = cls.get_module_data(module_name)
            
            if len(data) > ExportConstants.MAX_RECORDS_CSV:
                raise ValidationError(f"Dataset too large: {len(data)} records. Maximum allowed: {ExportConstants.MAX_RECORDS_CSV}")
            
            export_logger.info(f"CSV Export Started: {module_name} - {len(data)} records - User: {user.username}")
            
            return cls._generate_csv_response(module_name, data, user, start_time)
            
        except (PermissionDenied, ValidationError) as e:
            export_logger.warning(f"CSV export denied for {module_name}: {e} - User: {user.username}")
            return HttpResponse(str(e), status=403)
        except Exception as e:
            export_logger.error(f"CSV export failed for {module_name}: {e}")
            return HttpResponse(f'Export failed: {str(e)}', status=500)
    
    @classmethod
    def _generate_csv_response(cls, module_name, data, user, start_time):
        """Generate CSV response with proper error handling"""
        try:
            current_time = datetime.now()
            timestamp = current_time.strftime('%Y%m%d_%H%M')
            filename = cls._sanitize_filename(f"{module_name}_export_{timestamp}.csv")
            
            response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            writer = csv.writer(response)
            
            # Write metadata header
            writer.writerow([f'Exported on {current_time.strftime("%Y-%m-%d %H:%M:%S")} by {user.username}, Total Records: {len(data)}'])
            writer.writerow([])  # Empty row
            
            # Write headers
            headers = ExportConstants.CSV_HEADERS.get(module_name, ['Data'])
            writer.writerow(headers)
            
            # Pre-load fee report data for students
            if module_name == 'students' and data:
                fee_report_data = cls._get_fee_report_data()
                cls._fee_report_cache = {row.student_id: row.final_due for row in fee_report_data}
            
            # Write data rows with class separation for fees_report
            processed_count = 0
            if module_name == 'fees_report':
                current_class = None
                for i, item in enumerate(data):
                    try:
                        item_class = getattr(item, 'class_name', 'Unassigned')
                        
                        # Add class separator
                        if current_class != item_class:
                            if current_class is not None:  # Add empty row between classes
                                writer.writerow([])
                            writer.writerow([f'=== CLASS: {item_class} ==='])
                            current_class = item_class
                        
                        row_data = cls._get_csv_row_safe(module_name, item)
                        writer.writerow(row_data)
                        processed_count += 1
                    except Exception as e:
                        export_logger.warning(f"Error processing row {i} for {module_name}: {e}")
                        continue
            else:
                # Standard format for other modules
                for i, item in enumerate(data):
                    try:
                        row_data = cls._get_csv_row_safe(module_name, item)
                        
                        # Handle subjects module which returns multiple rows per item
                        if module_name == 'subjects' and isinstance(row_data, list) and len(row_data) > 0 and isinstance(row_data[0], list):
                            # Multiple rows returned
                            for row in row_data:
                                writer.writerow(row)
                                processed_count += 1
                        else:
                            # Single row returned
                            writer.writerow(row_data)
                            processed_count += 1
                    except Exception as e:
                        export_logger.warning(f"Error processing row {i} for {module_name}: {e}")
                        continue
            
            # Clean up cache
            if hasattr(cls, '_fee_report_cache'):
                delattr(cls, '_fee_report_cache')
            
            total_time = time.time() - start_time
            export_logger.info(
                f"CSV Export Complete: {module_name} - {filename} - "
                f"{processed_count}/{len(data)} records - {total_time:.3f}s - User: {user.username}"
            )
            
            return response
            
        except Exception as e:
            export_logger.error(f"CSV generation failed for {module_name}: {e}")
            return HttpResponse(f'Export failed: {str(e)}', status=500)
    
    @classmethod
    def _get_csv_row_safe(cls, module_name, item):
        """Get CSV row data with safe attribute access"""
        try:
            if module_name == 'students':
                # Get final due from centralized fee report calculation
                final_due = 0
                try:
                    student_id = getattr(item, 'id', None)
                    if student_id and hasattr(cls, '_fee_report_cache'):
                        final_due = cls._fee_report_cache.get(student_id, 0)
                    elif student_id:
                        fee_report_data = cls._get_fee_report_data()
                        for fee_row in fee_report_data:
                            if getattr(fee_row, 'student_id', None) == student_id:
                                final_due = getattr(fee_row, 'final_due', 0)
                                break
                except Exception:
                    final_due = 0
                
                return RowFormatter.format_student_row(item, final_due)
            elif module_name == 'teachers':
                return RowFormatter.format_teacher_row(item)
            elif module_name == 'subjects':
                # Handle multiple rows returned by format_subject_row
                rows = RowFormatter.format_subject_row(item)
                return rows  # Return all rows for this class section
            elif module_name == 'transport':
                return RowFormatter.format_transport_row(item)
            elif module_name == 'fees':
                return RowFormatter.format_fees_row(item)
            elif module_name == 'student_fees':
                return RowFormatter.format_student_fees_row(item)

            elif module_name == 'attendance':
                return RowFormatter.format_attendance_row(item)


            elif module_name == 'users':
                return RowFormatter.format_users_row(item)
            elif module_name == 'fees_report':
                return RowFormatter.format_fees_report_row(item)
            else:
                return [str(item)]
                
        except Exception as e:
            export_logger.error(f"Error processing CSV row for {module_name}: {e}")
            return ['Error processing data']