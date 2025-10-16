# promotion/services.py
from django.db import transaction
from django.core.cache import cache
from .models import PromotionRule, StudentPromotion
from students.models import Student
from subjects.models import ClassSection
import logging

logger = logging.getLogger(__name__)

class PromotionService:
    @staticmethod
    def get_eligible_students(from_class_section, minimum_percentage=0):
        """Get students eligible for promotion"""
        students = Student.objects.filter(class_section=from_class_section)
        
        # Filter by attendance/performance if needed
        eligible_students = []
        for student in students:
            # Add logic for eligibility criteria
            attendance_percentage = student.get_attendance_percentage()
            if attendance_percentage >= minimum_percentage:
                eligible_students.append(student)
        
        return eligible_students
    
    @staticmethod
    def bulk_promote_students(student_ids, from_class_id, to_class_id, academic_year, promotion_date=None):
        """Bulk promote students"""
        from django.utils import timezone
        
        if not promotion_date:
            promotion_date = timezone.now().date()
        
        from_class = ClassSection.objects.get(id=from_class_id)
        to_class = ClassSection.objects.get(id=to_class_id)
        
        promoted_count = 0
        
        with transaction.atomic():
            for student_id in student_ids:
                try:
                    student = Student.objects.select_for_update().get(id=student_id)
                    
                    # Create promotion record
                    StudentPromotion.objects.create(
                        student=student,
                        from_class_section=from_class,
                        to_class_section=to_class,
                        academic_year=academic_year,
                        promotion_date=promotion_date
                    )
                    
                    # Update student's class
                    student.class_section = to_class
                    student.save()
                    
                    promoted_count += 1
                    
                except Student.DoesNotExist:
                    logger.warning(f"Student {student_id} not found for promotion")
                    continue
        
        # Clear relevant caches
        cache.delete_pattern('student_stats*')
        
        return promoted_count
    
    @staticmethod
    def get_promotion_history(student):
        """Get promotion history for a student"""
        return StudentPromotion.objects.filter(student=student).order_by('-promotion_date')