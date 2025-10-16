# backup/services/export/row_formatters.py
"""Row formatting utilities for different export formats"""

import logging

export_logger = logging.getLogger('export.api')

class RowFormatter:
    """Utility class for formatting data rows"""
    
    @staticmethod
    def safe_get(obj, attr, default='N/A'):
        """Safely get attribute with default value"""
        try:
            value = getattr(obj, attr, default)
            return str(value) if value is not None else default
        except AttributeError:
            return default
    
    @staticmethod
    def safe_format_date(date_obj, format_str='%Y-%m-%d'):
        """Safely format date object"""
        try:
            return date_obj.strftime(format_str) if date_obj else 'N/A'
        except (AttributeError, ValueError):
            return 'N/A'
    
    @staticmethod
    def safe_slice(value, length):
        """Safely slice string value"""
        try:
            return str(value or '')[:length]
        except (AttributeError, TypeError):
            return 'N/A'
    
    @classmethod
    def format_student_row(cls, item, final_due=0):
        """Format student data row"""
        return [
            cls.safe_get(item, 'admission_number'),
            cls.safe_get(item, 'first_name'),
            cls.safe_get(item, 'last_name'),
            cls.safe_get(item, 'father_name'),
            cls.safe_get(item, 'mother_name'),
            cls.safe_format_date(getattr(item, 'date_of_birth', None)),
            cls.safe_format_date(getattr(item, 'date_of_admission', None)),
            cls.safe_get(item, 'gender'),
            cls.safe_get(item, 'religion'),
            cls.safe_get(item, 'caste_category'),
            cls.safe_get(item, 'mobile_number'),
            cls.safe_get(item, 'email'),
            cls.safe_get(item, 'address'),
            str(item.class_section) if hasattr(item, 'class_section') and item.class_section else 'N/A',
            cls.safe_get(item, 'aadhaar_number'),
            cls.safe_get(item, 'pen_number'),
            cls.safe_get(item, 'blood_group'),
            f"{getattr(item, 'attendance_percentage', 0):.1f}%",
            f"{float(final_due):.2f}"
        ]
    
    @classmethod
    def format_teacher_row(cls, item):
        """Format teacher data row"""
        return [
            cls.safe_get(item, 'id'),
            cls.safe_get(item, 'name'),
            cls.safe_get(item, 'mobile'),
            cls.safe_get(item, 'email'),
            cls.safe_get(item, 'qualification'),
            cls.safe_format_date(getattr(item, 'joining_date', None))
        ]
    
    @classmethod
    def format_fees_report_row(cls, item):
        """Format fee report data row"""
        return [
            cls.safe_get(item, 'name'),
            cls.safe_get(item, 'admission_number'),
            cls.safe_get(item, 'class_name'),
            f"{getattr(item, 'current_fees', 0):.2f}",
            f"{getattr(item, 'current_paid', 0):.2f}",
            f"{getattr(item, 'current_discount', 0):.2f}",
            f"{getattr(item, 'cf_due', 0):.2f}",
            f"{getattr(item, 'fine_paid', 0):.2f}",
            f"{getattr(item, 'fine_unpaid', 0):.2f}",
            f"{getattr(item, 'final_due', 0):.2f}",
            'Paid' if getattr(item, 'final_due', 0) == 0 else 'Outstanding',
            cls.safe_get(item, 'mobile_number'),
            cls.safe_get(item, 'email')
        ]
    
    @classmethod
    def format_student_row_compact(cls, student, fee_lookup):
        """Format student row for PDF (compact)"""
        student_id = getattr(student, 'id', None)
        final_due = fee_lookup.get(student_id, 0) if student_id else 0
        
        return [
            cls.safe_slice(getattr(student, 'admission_number', ''), 8),
            f"{getattr(student, 'first_name', '')} {getattr(student, 'last_name', '')}"[:15],
            cls.safe_slice(getattr(student, 'father_name', ''), 12),
            cls.safe_slice(getattr(student, 'mother_name', ''), 12),
            cls.safe_slice(str(student.class_section) if hasattr(student, 'class_section') and student.class_section else 'N/A', 8),
            cls.safe_slice(getattr(student, 'mobile_number', ''), 10),
            f"{float(final_due):.0f}"
        ]
    
    @classmethod
    def format_subject_row(cls, item):
        """Format comprehensive combined subject data row with class-subject-teacher relationships"""
        # Get student count
        student_count = 'N/A'
        try:
            if hasattr(item, 'students'):
                student_count = item.students.count()
            elif hasattr(item, '_prefetched_objects_cache') and 'students' in item._prefetched_objects_cache:
                student_count = len(item._prefetched_objects_cache['students'])
        except Exception:
            student_count = 'N/A'
        
        # Get subject assignments for this class section
        subject_assignments = []
        try:
            from subjects.models import SubjectAssignment
            assignments = SubjectAssignment.objects.filter(
                class_section=item
            ).select_related('subject', 'teacher')
            
            for assignment in assignments:
                subject_name = cls.safe_get(assignment.subject, 'name') if hasattr(assignment, 'subject') and assignment.subject else 'N/A'
                teacher_name = cls.safe_get(assignment.teacher, 'name') if hasattr(assignment, 'teacher') and assignment.teacher else 'Unassigned'
                assignment_status = 'Active' if hasattr(assignment, 'is_active') and getattr(assignment, 'is_active', True) else 'Inactive'
                created_date = cls.safe_format_date(getattr(assignment, 'created_at', None))
                
                subject_assignments.append({
                    'subject': subject_name,
                    'teacher': teacher_name,
                    'status': assignment_status,
                    'created_date': created_date
                })
        except Exception as e:
            # Fallback: create a default academic entry
            subject_assignments = [{
                'subject': 'Academic Subjects',
                'teacher': 'To be assigned',
                'status': 'Active',
                'created_date': cls.safe_format_date(getattr(item, 'created_at', None))
            }]
        
        # If no subject assignments found, create default entry
        if not subject_assignments:
            subject_assignments = [{
                'subject': 'General Studies',
                'teacher': 'Class Teacher',
                'status': 'Active',
                'created_date': cls.safe_format_date(getattr(item, 'created_at', None))
            }]
        
        # Create rows for each subject assignment (Option A: Combined Format)
        rows = []
        for assignment in subject_assignments:
            row = [
                cls.safe_get(item, 'class_name'),           # Class Name
                cls.safe_get(item, 'section_name'),         # Section
                cls.safe_get(item, 'room_number'),          # Room Number
                str(student_count),                         # Student Count
                assignment['subject'],                      # Subject
                assignment['teacher'],                      # Teacher
                assignment['status'],                       # Assignment Status
                assignment['created_date']                  # Created Date
            ]
            rows.append(row)
        
        return rows
    
    @classmethod
    def format_transport_row(cls, item):
        """Format transport assignment data row"""
        return [
            f"{cls.safe_get(item.student, 'first_name')} {cls.safe_get(item.student, 'last_name')}" if hasattr(item, 'student') and item.student else 'N/A',
            cls.safe_get(item.student, 'admission_number') if hasattr(item, 'student') and item.student else 'N/A',
            str(item.student.class_section) if hasattr(item, 'student') and item.student and hasattr(item.student, 'class_section') and item.student.class_section else 'N/A',
            cls.safe_get(item.route, 'name') if hasattr(item, 'route') and item.route else 'N/A',
            cls.safe_get(item.stoppage, 'name') if hasattr(item, 'stoppage') and item.stoppage else 'N/A',
            '',  # Empty Pickup Time for manual entry
            cls.safe_format_date(getattr(item, 'assigned_date', None)),
            'Active',  # Status
            cls.safe_get(item.student, 'mobile_number') if hasattr(item, 'student') and item.student else 'N/A',
            cls.safe_get(item.student, 'address') if hasattr(item, 'student') and item.student else 'N/A'
        ]
    
    @classmethod
    def format_fees_row(cls, item):
        """Format fees type data row with student count"""
        # Calculate student count for this fee type
        student_count = 0
        try:
            from students.models import Student
            from subjects.models import ClassSection
            
            if hasattr(item, 'class_name') and item.class_name:
                # Split comma-separated class names and count for each
                class_names = [name.strip() for name in item.class_name.split(',')]
                for class_name in class_names:
                    # Find matching ClassSection objects first, then count students
                    matching_sections = ClassSection.objects.filter(
                        class_name__iexact=class_name
                    )
                    
                    # If no exact match, try parsing "Class 10A" format
                    if not matching_sections.exists() and len(class_name) > 6:
                        import re
                        # Extract class and section from "Class 10A" format
                        match = re.match(r'(.*?)([A-Z])$', class_name)
                        if match:
                            base_class = match.group(1).strip()
                            section = match.group(2)
                            matching_sections = ClassSection.objects.filter(
                                class_name__iexact=base_class,
                                section_name__iexact=section
                            )
                    
                    # Count students in matching sections
                    for section in matching_sections:
                        student_count += Student.objects.filter(class_section=section).count()
                        
            elif hasattr(item, 'related_stoppage') and item.related_stoppage:
                from transport.models import TransportAssignment
                student_count = TransportAssignment.objects.filter(
                    stoppage=item.related_stoppage
                ).count()
        except Exception:
            student_count = 0
        
        # Get proper fee group name from the FeesGroup relationship
        fee_group_name = 'N/A'
        if hasattr(item, 'fee_group') and item.fee_group:
            # Access the fee_group field from FeesGroup model
            fee_group_name = cls.safe_get(item.fee_group, 'fee_group')
            if fee_group_name == 'N/A':
                fee_group_name = str(item.fee_group)
        
        return [
            fee_group_name,
            cls.safe_get(item.fee_group, 'group_type') if hasattr(item, 'fee_group') and item.fee_group else 'N/A',
            cls.safe_get(item.fee_group, 'fee_type') if hasattr(item, 'fee_group') and item.fee_group else 'N/A',
            cls.safe_get(item, 'amount_type'),
            cls.safe_get(item, 'month_name'),
            cls.safe_get(item, 'class_name'),
            cls.safe_get(item, 'stoppage_name'),
            cls.safe_get(item, 'amount'),
            str(student_count)
        ]
    
    @classmethod
    def format_student_fees_row(cls, item):
        """Format grouped student fee deposit data row (Receipt-Grouped Format)"""
        # Create fee breakdown string
        fee_breakdown = []
        if hasattr(item, 'deposits'):
            for deposit in item.deposits:
                note = cls.safe_get(deposit, 'note', '')
                amount = cls.safe_get(deposit, 'amount', 0)
                # Extract fee type from note or use generic description
                if 'Fine' in note:
                    fee_type = 'Fine'
                elif 'Transport' in note:
                    fee_type = 'Transport'
                elif 'Tuition' in note:
                    fee_type = 'Tuition Fee'
                elif 'Exam' in note:
                    fee_type = 'Exam Fee'
                elif 'Carry Forward' in note:
                    fee_type = 'Carry Forward'
                else:
                    fee_type = 'Fee Payment'
                
                fee_breakdown.append(f"{fee_type}: Rs.{float(amount):.2f}")
        
        fee_breakdown_str = ', '.join(fee_breakdown) if fee_breakdown else 'Fee Payment'
        
        return [
            cls.safe_get(item, 'receipt_no'),
            f"{cls.safe_get(item.student, 'first_name')} {cls.safe_get(item.student, 'last_name')}" if hasattr(item, 'student') and item.student else 'N/A',
            cls.safe_format_date(getattr(item, 'deposit_date', None)),
            cls.safe_get(item, 'payment_mode'),
            cls.safe_get(item, 'transaction_no'),
            fee_breakdown_str,
            f"Rs.{float(getattr(item, 'total_amount', 0)):.2f}",
            f"Rs.{float(getattr(item, 'total_discount', 0)):.2f}",
            f"Rs.{float(getattr(item, 'total_paid', 0)):.2f}",
            cls.safe_get(item, 'payment_source')
        ]
    
    @classmethod
    def format_fines_row(cls, item):
        """Format fines data row"""
        return [
            cls.safe_get(item.fine_type, 'fine_type') if hasattr(item, 'fine_type') and item.fine_type else 'N/A',
            cls.safe_get(item.fine_type, 'category') if hasattr(item, 'fine_type') and item.fine_type else 'N/A',
            cls.safe_get(item.fine_type, 'target_scope') if hasattr(item, 'fine_type') and item.fine_type else 'N/A',
            cls.safe_get(item, 'amount'),
            cls.safe_get(item.fine_type, 'dynamic_percentage') if hasattr(item, 'fine_type') and item.fine_type else 0,
            cls.safe_get(item, 'reason'),
            cls.safe_format_date(getattr(item, 'due_date', None)),
            cls.safe_format_date(getattr(item, 'applied_date', None)),
            'Yes' if getattr(item, 'auto_generated', False) else 'No',
            cls.safe_get(item.created_by, 'username') if hasattr(item, 'created_by') and item.created_by else 'N/A',
            str(item.class_section) if hasattr(item, 'class_section') and item.class_section else 'N/A'
        ]
    
    @classmethod
    def format_attendance_row(cls, item):
        """Format attendance data row with separators and proper class section"""
        # Handle separators
        if hasattr(item, 'is_separator') and item.is_separator:
            if item.separator_type == 'month':
                return [f"=== {item.separator_text} ===", '', '', '', '']
            elif item.separator_type == 'date':
                return [f"--- {item.separator_text} ---", '', '', '', '']
            elif item.separator_type == 'class':
                return [f">> {item.separator_text} <<", '', '', '', '']
        
        # Get proper class section
        class_section = 'N/A'
        if hasattr(item, 'class_section') and item.class_section:
            class_section = str(item.class_section)
        elif hasattr(item, 'student') and item.student and hasattr(item.student, 'class_section') and item.student.class_section:
            class_section = str(item.student.class_section)
        
        # Handle status field properly
        status = cls.safe_get(item, 'status', 'Absent')
        if status not in ['Present', 'Absent']:
            status = 'Present' if status == 'Present' else 'Absent'
        
        return [
            f"{cls.safe_get(item.student, 'first_name')} {cls.safe_get(item.student, 'last_name')}" if hasattr(item, 'student') and item.student else 'N/A',
            class_section,
            cls.safe_format_date(getattr(item, 'date', None)),
            status,
            cls.safe_format_date(getattr(item, 'created_at', None), '%Y-%m-%d %H:%M')
        ]
    
    @classmethod
    def format_promotion_row(cls, item):
        """Format promotion data row"""
        return [
            f"{cls.safe_get(item.student, 'first_name')} {cls.safe_get(item.student, 'last_name')}" if hasattr(item, 'student') and item.student else 'N/A',
            str(item.from_class_section) if hasattr(item, 'from_class_section') and item.from_class_section else 'N/A',
            str(item.to_class_section) if hasattr(item, 'to_class_section') and item.to_class_section else 'N/A',
            cls.safe_get(item, 'academic_year'),
            cls.safe_format_date(getattr(item, 'promotion_date', None)),
            cls.safe_get(item, 'remarks'),
            cls.safe_get(item, 'min_percentage')
        ]
    
    @classmethod
    def format_messaging_row(cls, item):
        """Format messaging data row"""
        return [
            cls.safe_get(item.sender, 'username') if hasattr(item, 'sender') and item.sender else 'N/A',
            cls.safe_get(item, 'message_type'),
            cls.safe_get(item, 'recipient_type'),
            cls.safe_get(item, 'content')[:100] + '...' if len(cls.safe_get(item, 'content', '')) > 100 else cls.safe_get(item, 'content'),
            cls.safe_get(item, 'total_recipients'),
            cls.safe_get(item, 'successful_count'),
            cls.safe_get(item, 'failed_count'),
            cls.safe_get(item, 'status'),
            cls.safe_get(item, 'source_module'),
            cls.safe_format_date(getattr(item, 'created_at', None), '%Y-%m-%d %H:%M')
        ]
    
    @classmethod
    def format_users_row(cls, item):
        """Format users data row with role hierarchy and proper formatting"""
        # Get proper role display with hierarchy consideration
        role_display = 'User'
        if getattr(item, 'is_superuser', False):
            role_display = 'Super User'
        elif hasattr(item, 'role') and item.role:
            role_display = item.role.title()
        elif getattr(item, 'is_staff', False):
            role_display = 'Staff'
        
        return [
            cls.safe_get(item, 'username'),
            cls.safe_get(item, 'email'),
            role_display,
            cls.safe_get(item, 'mobile'),
            'Yes' if getattr(item, 'is_active', False) else 'No',
            'Yes' if getattr(item, 'is_staff', False) else 'No',
            'Yes' if getattr(item, 'is_superuser', False) else 'No',
            cls.safe_format_date(getattr(item, 'date_joined', None)),
            cls.safe_format_date(getattr(item, 'last_login', None), '%Y-%m-%d %H:%M') if getattr(item, 'last_login', None) else 'Never'
        ]