# backup/services/export/data_fetchers.py
"""Data fetching utilities for different modules"""

import logging
from collections import defaultdict

export_logger = logging.getLogger('export.api')

class DataFetcher:
    """Utility class for fetching module data"""
    
    @classmethod
    def get_students_data(cls):
        """Get optimized student data"""
        from students.models import Student
        return Student.objects.get_list_optimized()
    
    @classmethod
    def get_teachers_data(cls):
        """Get teacher data"""
        from teachers.models import Teacher
        return list(Teacher.objects.all())
    
    @classmethod
    def get_subjects_data(cls):
        """Get class section data"""
        from subjects.models import ClassSection
        return list(ClassSection.objects.ordered())
    
    @classmethod
    def get_transport_data(cls):
        """Get transport assignment data"""
        from transport.models import TransportAssignment
        return list(TransportAssignment.objects.select_related('student', 'route', 'stoppage'))
    
    @classmethod
    def get_fees_data(cls):
        """Get fees type data"""
        from fees.models import FeesType
        return list(FeesType.objects.select_related('fee_group').all())
    
    @classmethod
    def get_student_fees_data(cls):
        """Get fee deposit data"""
        from student_fees.models import FeeDeposit
        return list(FeeDeposit.objects.select_related('student').order_by('-deposit_date'))
    
    @classmethod
    def get_fines_data(cls):
        """Get fines data"""
        from fines.models import Fine
        return list(Fine.objects.select_related('fine_type', 'class_section', 'created_by').all())
    
    @classmethod
    def get_attendance_data(cls):
        """Get attendance data"""
        from attendance.models import Attendance
        return list(Attendance.objects.select_related('student', 'class_section'))
    
    @classmethod
    def get_promotion_data(cls):
        """Get promotion data"""
        from promotion.models import StudentPromotion
        return list(StudentPromotion.objects.select_related('student', 'from_class_section', 'to_class_section'))
    
    @classmethod
    def get_messaging_data(cls):
        """Get messaging data"""
        from messaging.models import MessageLog
        return list(MessageLog.objects.select_related('sender', 'class_section_filter').all())
    
    @classmethod
    def get_users_data(cls):
        """Get users data"""
        from users.models import CustomUser
        return list(CustomUser.objects.all().order_by('username'))
    
    @classmethod
    def organize_by_class(cls, students):
        """Organize students by class"""
        return sorted(students, key=lambda s: (s.class_section.class_name if s.class_section else 'No Class', s.first_name))