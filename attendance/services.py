# attendance/services.py
from django.db.models import Count, Q
from django.core.cache import cache
from django.utils import timezone
from .models import Attendance
from students.models import Student
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class AttendanceService:
    @staticmethod
    def calculate_attendance_percentage(student, start_date=None, end_date=None):
        """Calculate attendance percentage for a student"""
        queryset = Attendance.objects.filter(student=student)
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        total = queryset.count()
        present = queryset.filter(status='Present').count()
        
        return round((present / total * 100), 2) if total > 0 else 0
    
    @staticmethod
    def get_class_attendance_summary(class_section, date):
        """Get attendance summary for a class on specific date"""
        cache_key = f"attendance_summary_{class_section.id}_{date}"
        summary = cache.get(cache_key)
        
        if not summary:
            students = Student.objects.filter(class_section=class_section)
            attendance_records = Attendance.objects.filter(
                student__class_section=class_section,
                date=date
            )
            
            total_students = students.count()
            present_count = attendance_records.filter(status='Present').count()
            absent_count = attendance_records.filter(status='Absent').count()
            
            summary = {
                'total_students': total_students,
                'present': present_count,
                'absent': absent_count,
                'percentage': round((present_count / total_students * 100), 2) if total_students > 0 else 0
            }
            cache.set(cache_key, summary, 3600)  # 1 hour
        
        return summary
    
    @staticmethod
    def bulk_mark_attendance(class_section, date, attendance_data):
        """Bulk mark attendance for a class"""
        # Delete existing records
        Attendance.objects.filter(
            student__class_section=class_section,
            date=date
        ).delete()
        
        # Create new records
        attendance_records = []
        for item in attendance_data:
            student = Student.objects.get(id=item['student_id'])
            attendance_records.append(Attendance(
                student=student,
                date=date,
                status=item['status']
            ))
        
        Attendance.objects.bulk_create(attendance_records)
        
        # Clear cache
        cache.delete(f"attendance_summary_{class_section.id}_{date}")
        
        return len(attendance_records)