# backup/services/export/base.py
"""Base export service with common functionality"""

import logging
import time
import os
from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models
from collections import defaultdict
import traceback

class FeeReportRow:
    """Proper class for fee report row data to avoid pickle issues"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
from decimal import Decimal

from .constants import ExportConstants

export_logger = logging.getLogger('export.api')

class DataExportService:
    """Base export service with common functionality"""
    
    SUPPORTED_MODULES = {
        'students': 'students.models.Student',
        'teachers': 'teachers.models.Teacher', 
        'subjects': 'subjects.models.ClassSection',
        'transport': 'transport.models.TransportAssignment',
        'fees': 'fees.models.FeesGroup',
        'student_fees': 'student_fees.models.FeeDeposit',
        'attendance': 'attendance.models.Attendance',
        'users': 'users.models.CustomUser',
        'fees_report': 'custom_fee_report'
    }
    
    @classmethod
    def _validate_user_permissions(cls, user, module_name):
        """Validate user permissions using server-side session data"""
        if not user.is_authenticated:
            raise PermissionDenied("Authentication required")
        
        if user.is_superuser:
            return True
        
        from users.models import UserModulePermission
        permissions = UserModulePermission.get_user_permissions(user)
        
        module_perms = permissions.get(module_name, {})
        if not module_perms.get('view', False):
            raise PermissionDenied(f"Export permission denied for {module_name} module")
        
        return True
    
    @classmethod
    def _sanitize_filename(cls, filename):
        """Sanitize filename to prevent path traversal"""
        import re
        filename = os.path.basename(filename)
        filename = re.sub(r'[^\w\-_\.]', '_', filename)
        return filename[:100]
    
    @classmethod
    def get_module_data(cls, module_name):
        """Get data using existing optimized managers"""
        start_time = time.time()
        export_logger.info(f"Fetching {module_name} data for export")
        
        try:
            if module_name == 'students':
                from students.models import Student
                data = Student.objects.select_related('class_section').all()
                return cls._organize_students_by_class_and_name(data)
            elif module_name == 'teachers':
                from teachers.models import Teacher
                return list(Teacher.objects.all().order_by('name'))
            elif module_name == 'subjects':
                from subjects.models import ClassSection
                return list(ClassSection.objects.select_related().prefetch_related('students').all())
            elif module_name == 'transport':
                from transport.models import TransportAssignment
                data = TransportAssignment.objects.select_related('student', 'route', 'stoppage', 'student__class_section').all()
                return cls._organize_transport_by_class(data)
            elif module_name == 'fees':
                from fees.models import FeesType
                return list(FeesType.objects.select_related('fee_group').all())
            elif module_name == 'student_fees':
                from student_fees.models import FeeDeposit
                from collections import defaultdict
                
                # Get all fee deposits grouped by receipt
                deposits = FeeDeposit.objects.select_related('student').order_by('-deposit_date')
                
                # Group by receipt number
                receipt_groups = defaultdict(list)
                for deposit in deposits:
                    receipt_no = deposit.receipt_no or f"MANUAL_{deposit.id}"
                    receipt_groups[receipt_no].append(deposit)
                
                # Create grouped receipt objects
                grouped_receipts = []
                for receipt_no, deposits_list in receipt_groups.items():
                    first_deposit = deposits_list[0]
                    
                    class GroupedReceipt:
                        def __init__(self):
                            self.receipt_no = receipt_no
                            self.student = first_deposit.student
                            self.deposit_date = first_deposit.deposit_date
                            self.payment_mode = first_deposit.payment_mode
                            self.transaction_no = first_deposit.transaction_no or ''
                            self.payment_source = first_deposit.payment_source or ''
                            self.deposits = deposits_list
                            self.total_amount = sum(float(d.amount or 0) for d in deposits_list)
                            self.total_discount = sum(float(d.discount or 0) for d in deposits_list)
                            self.total_paid = sum(float(d.paid_amount or 0) for d in deposits_list)
                    
                    grouped_receipts.append(GroupedReceipt())
                
                return grouped_receipts

            elif module_name == 'attendance':
                from attendance.models import Attendance
                data = Attendance.objects.select_related('student', 'student__class_section', 'class_section').all()
                return cls._organize_attendance_by_month_date_class(data)


            elif module_name == 'users':
                from users.models import CustomUser
                # Sort by role hierarchy: superuser → admin → teacher → student → others, then by username
                return cls._organize_users_by_role_hierarchy(CustomUser.objects.all())
            elif module_name == 'fees_report':
                return cls._get_fee_report_data()
            return []
        except Exception as e:
            fetch_time = time.time() - start_time
            export_logger.error(f"Error fetching {module_name} data: {e}")
            return []
        finally:
            fetch_time = time.time() - start_time
            export_logger.info(f"Fetched {module_name} data in {fetch_time:.2f}s")
    
    @classmethod
    def _organize_students_by_class_and_name(cls, students):
        """Organize students by class hierarchy and alphabetically by name"""
        def get_class_order(class_name):
            if not class_name:
                return (999, 'Unassigned')
            
            class_name = class_name.upper()
            if 'NURSERY' in class_name:
                return (0, 'Nursery')
            elif 'LKG' in class_name:
                return (1, 'LKG')
            elif 'UKG' in class_name:
                return (2, 'UKG')
            elif 'CLASS' in class_name or 'STD' in class_name:
                try:
                    import re
                    match = re.search(r'(\d+)', class_name)
                    if match:
                        num = int(match.group(1))
                        return (2 + num, f'Class {num}')
                except:
                    pass
            return (900, class_name)
        
        return sorted(students, key=lambda s: (
            get_class_order(s.class_section.class_name if s.class_section else None)[0],
            s.first_name or '',
            s.last_name or ''
        ))
    
    @classmethod
    def _organize_attendance_by_month_date_class(cls, attendance_records):
        """Organize attendance by month, then date, then class section with proper separators"""
        from collections import defaultdict
        import calendar
        
        # Group by month, then date, then class
        monthly_data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        
        for record in attendance_records:
            # Get proper class section
            class_section = None
            if hasattr(record, 'class_section') and record.class_section:
                class_section = record.class_section
            elif hasattr(record, 'student') and record.student and hasattr(record.student, 'class_section') and record.student.class_section:
                class_section = record.student.class_section
            
            class_name = str(class_section) if class_section else 'Unassigned'
            
            # Group by month-year, date, class
            month_key = record.date.strftime('%Y-%m') if record.date else '0000-00'
            date_key = record.date.strftime('%Y-%m-%d') if record.date else '0000-00-00'
            
            monthly_data[month_key][date_key][class_name].append(record)
        
        # Create organized list with separators
        organized_records = []
        
        for month_key in sorted(monthly_data.keys(), reverse=True):  # Newest month first
            month_data = monthly_data[month_key]
            
            # Add month separator
            if month_key != '0000-00':
                try:
                    year, month = month_key.split('-')
                    month_name = calendar.month_name[int(month)]
                    month_separator = type('MonthSeparator', (), {
                        'is_separator': True,
                        'separator_type': 'month',
                        'separator_text': f"{month_name} {year}",
                        'date': None,
                        'student': None,
                        'class_section': None,
                        'status': None,
                        'created_at': None
                    })()
                    organized_records.append(month_separator)
                except:
                    pass
            
            for date_key in sorted(month_data.keys(), reverse=True):  # Newest date first
                date_data = month_data[date_key]
                
                # Add date separator
                if date_key != '0000-00-00':
                    date_separator = type('DateSeparator', (), {
                        'is_separator': True,
                        'separator_type': 'date',
                        'separator_text': f"Date: {date_key}",
                        'date': None,
                        'student': None,
                        'class_section': None,
                        'status': None,
                        'created_at': None
                    })()
                    organized_records.append(date_separator)
                
                # Sort classes by hierarchy
                sorted_classes = sorted(date_data.keys(), key=lambda x: cls._get_class_sort_order(x))
                
                for class_name in sorted_classes:
                    class_records = date_data[class_name]
                    
                    # Add class separator
                    class_separator = type('ClassSeparator', (), {
                        'is_separator': True,
                        'separator_type': 'class',
                        'separator_text': f"Class: {class_name}",
                        'date': None,
                        'student': None,
                        'class_section': None,
                        'status': None,
                        'created_at': None
                    })()
                    organized_records.append(class_separator)
                    
                    # Sort students alphabetically within class
                    sorted_records = sorted(class_records, key=lambda r: (
                        r.student.first_name if r.student and r.student.first_name else '',
                        r.student.last_name if r.student and r.student.last_name else ''
                    ))
                    
                    organized_records.extend(sorted_records)
        
        return organized_records
    
    @classmethod
    def _get_class_sort_order(cls, class_name):
        """Get sorting order for class names"""
        if not class_name or class_name == 'Unassigned':
            return (999, 'Unassigned')
        
        class_name = str(class_name).upper()
        if 'NURSERY' in class_name:
            return (0, 'Nursery')
        elif 'LKG' in class_name:
            return (1, 'LKG')
        elif 'UKG' in class_name:
            return (2, 'UKG')
        elif 'CLASS' in class_name or any(char.isdigit() for char in class_name):
            try:
                import re
                match = re.search(r'(\d+)', class_name)
                if match:
                    num = int(match.group(1))
                    return (2 + num, f'Class {num}')
            except:
                pass
        return (900, class_name)
    
    @classmethod
    def _organize_users_by_role_hierarchy(cls, users):
        """Organize users by role hierarchy: superuser → admin → teacher → student → others"""
        def get_role_order(user):
            if getattr(user, 'is_superuser', False):
                return (0, 'superuser')
            elif hasattr(user, 'role') and user.role == 'admin':
                return (1, 'admin')
            elif hasattr(user, 'role') and user.role == 'teacher':
                return (2, 'teacher')
            elif hasattr(user, 'role') and user.role == 'student':
                return (3, 'student')
            elif getattr(user, 'is_staff', False):
                return (4, 'staff')
            else:
                return (5, 'user')
        
        return sorted(users, key=lambda u: (
            get_role_order(u)[0],
            u.username or ''
        ))
    
    @classmethod
    def _organize_transport_by_class(cls, assignments):
        """Organize transport assignments by class hierarchy"""
        def get_class_order(class_name):
            if not class_name:
                return (999, 'Unassigned')
            
            class_name = class_name.upper()
            if 'NURSERY' in class_name:
                return (0, 'Nursery')
            elif 'LKG' in class_name:
                return (1, 'LKG')
            elif 'UKG' in class_name:
                return (2, 'UKG')
            elif 'CLASS' in class_name or 'STD' in class_name:
                try:
                    import re
                    match = re.search(r'(\d+)', class_name)
                    if match:
                        num = int(match.group(1))
                        return (2 + num, f'Class {num}')
                except:
                    pass
            return (900, class_name)
        
        return sorted(assignments, key=lambda a: (
            get_class_order(a.student.class_section.class_name if a.student and a.student.class_section else None)[0],
            a.student.first_name if a.student else '',
            a.student.last_name if a.student else ''
        ))
    
    @classmethod
    def _get_fee_report_data(cls):
        """Get fee report data using existing reports view logic with error handling"""
        try:
            from decimal import Decimal
            from django.db.models import Sum, Q
            from students.models import Student
            from student_fees.models import FeeDeposit
            from fees.models import FeesType
            from transport.models import TransportAssignment
            
            students = Student.objects.select_related('class_section').all()
            raw_data = []
            
            for student in students:
                try:
                    class_name = student.class_section.class_name if student.class_section else ''
                    class_display = student.class_section.display_name if student.class_section else ''
                    
                    # Get applicable current session fees with safe query
                    try:
                        applicable_fees = FeesType.objects.filter(
                            Q(class_name__isnull=True) | 
                            Q(class_name__iexact=class_name) |
                            Q(class_name__iexact=class_display)
                        ).exclude(fee_group__group_type="Transport")
                        
                        # Add transport fees if assigned
                        transport_assignment = TransportAssignment.objects.filter(student=student).first()
                        if transport_assignment and transport_assignment.stoppage:
                            transport_fees = FeesType.objects.filter(
                                fee_group__group_type="Transport",
                                related_stoppage=transport_assignment.stoppage
                            )
                            applicable_fees = list(applicable_fees) + list(transport_fees)
                        
                        # Calculate current session fees
                        current_fees = sum(Decimal(str(fee.amount)) for fee in applicable_fees)
                    except Exception as e:
                        export_logger.warning(f"Error calculating fees for student {student.id}: {e}")
                        current_fees = Decimal('0')
                    
                    # Carry Forward amounts with safe access
                    cf_due_original = Decimal(str(getattr(student, 'due_amount', 0) or 0))
                    
                    # Total fees = Current session fees + Carry forward due
                    total_fees = current_fees + cf_due_original
                    
                    # Get payments with safe query
                    try:
                        fee_payments = FeeDeposit.objects.filter(
                            student=student
                        ).exclude(note__icontains="Fine Payment")
                        
                        total_fee_paid = fee_payments.aggregate(Sum('paid_amount'))['paid_amount__sum'] or Decimal('0')
                        total_fee_discount = fee_payments.aggregate(Sum('discount'))['discount__sum'] or Decimal('0')
                        
                        # Separate CF payments for display
                        cf_payments = fee_payments.filter(
                            Q(note__icontains="Carry Forward") | Q(payment_source="carry_forward")
                        )
                        cf_paid = cf_payments.aggregate(Sum('paid_amount'))['paid_amount__sum'] or Decimal('0')
                        cf_discount = cf_payments.aggregate(Sum('discount'))['discount__sum'] or Decimal('0')
                        
                        # Remaining CF due
                        cf_due = max(cf_due_original - cf_paid - cf_discount, Decimal('0'))
                    except Exception as e:
                        export_logger.warning(f"Error calculating payments for student {student.id}: {e}")
                        total_fee_paid = total_fee_discount = cf_due = Decimal('0')
                    
                    # Fine amounts with safe handling
                    fine_paid = fine_unpaid = Decimal('0')
                    try:
                        from fines.models import FineStudent
                        unpaid_fines = FineStudent.objects.filter(
                            student=student, 
                            is_paid=False
                        ).select_related('fine')
                        
                        paid_fines = FineStudent.objects.filter(
                            student=student, 
                            is_paid=True
                        ).select_related('fine')
                        
                        fine_unpaid = sum(Decimal(str(fs.fine.amount)) for fs in unpaid_fines)
                        fine_paid = sum(Decimal(str(fs.fine.amount)) for fs in paid_fines)
                    except Exception as e:
                        export_logger.warning(f"Error calculating fines for student {student.id}: {e}")
                        fine_unpaid = fine_paid = Decimal('0')
                    
                    # Calculate final due: Total fees - Total paid - Total discount + Unpaid fines
                    final_due = max(total_fees - total_fee_paid - total_fee_discount + fine_unpaid, Decimal('0'))
                    
                    # Create row object with proper class to avoid pickle issues
                    row = FeeReportRow(
                        name=f"{getattr(student, 'first_name', '') or ''} {getattr(student, 'last_name', '') or ''}".strip() or 'Unknown',
                        admission_number=getattr(student, 'admission_number', '') or '',
                        class_name=str(student.class_section) if student.class_section else 'Unassigned',
                        current_fees=float(total_fees),
                        current_paid=float(total_fee_paid),
                        current_discount=float(total_fee_discount),
                        cf_due=float(cf_due),
                        fine_paid=float(fine_paid),
                        fine_unpaid=float(fine_unpaid),
                        final_due=float(final_due),
                        mobile_number=getattr(student, 'mobile_number', '') or '',
                        email=getattr(student, 'email', '') or '',
                        student_id=student.id
                    )
                    
                    raw_data.append(row)
                    
                except Exception as e:
                    export_logger.error(f"Error processing student {student.id}: {e}")
                    # Create minimal row for failed student
                    row = FeeReportRow(
                        name=f"{getattr(student, 'first_name', '') or ''} {getattr(student, 'last_name', '') or ''}".strip() or 'Unknown',
                        admission_number=getattr(student, 'admission_number', '') or '',
                        class_name=str(student.class_section) if student.class_section else 'Unassigned',
                        current_fees=0.0,
                        current_paid=0.0,
                        current_discount=0.0,
                        cf_due=0.0,
                        fine_paid=0.0,
                        fine_unpaid=0.0,
                        final_due=0.0,
                        mobile_number=getattr(student, 'mobile_number', '') or '',
                        email=getattr(student, 'email', '') or '',
                        student_id=student.id
                    )
                    raw_data.append(row)
                    continue
            
            return cls._organize_fee_report_by_class(raw_data)
            
        except Exception as e:
            export_logger.error(f"Critical error in fee report data generation: {e}")
            return []
    
    @classmethod
    def _organize_fee_report_by_class(cls, report_data):
        """Organize fee report data by class hierarchy (Nursery -> LKG -> UKG -> Class 1-10) with clear separation"""
        def get_class_order(class_name):
            if not class_name or class_name == 'Unassigned':
                return (999, 'Unassigned')
            
            class_name = str(class_name).upper()
            if 'NURSERY' in class_name:
                return (0, 'Nursery')
            elif 'LKG' in class_name:
                return (1, 'LKG')
            elif 'UKG' in class_name:
                return (2, 'UKG')
            elif 'CLASS' in class_name or any(char.isdigit() for char in class_name):
                try:
                    import re
                    match = re.search(r'(\d+)', class_name)
                    if match:
                        num = int(match.group(1))
                        return (2 + num, f'Class {num}')
                except:
                    pass
            return (900, class_name)
        
        try:
            # Group by class with safe access
            class_groups = defaultdict(list)
            for row in report_data:
                class_name = getattr(row, 'class_name', 'Unassigned') or 'Unassigned'
                class_groups[class_name].append(row)
            
            # Sort classes by hierarchy and students alphabetically within each class
            organized_data = []
            sorted_classes = sorted(class_groups.keys(), key=lambda x: get_class_order(x)[0])
            
            for class_name in sorted_classes:
                students = sorted(class_groups[class_name], key=lambda x: getattr(x, 'name', '') or '')
                organized_data.extend(students)
            
            return organized_data
        except Exception as e:
            export_logger.error(f"Error organizing fee report data: {e}")
            return report_data  # Return unsorted data as fallback