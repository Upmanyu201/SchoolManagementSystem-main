"""
Utility functions for handling student promotions and fine cleanup
"""
from fines.models import FineStudent
import logging

logger = logging.getLogger(__name__)

def cleanup_irrelevant_fines_after_promotion(student):
    """
    Clean up FineStudent records that are no longer relevant after student promotion.
    Only removes unpaid class-specific fines that don't match the student's new class.
    """
    try:
        # Get all unpaid FineStudent records for this student
        unpaid_fine_students = FineStudent.objects.filter(
            student=student,
            is_paid=False,
            fine__is_active=True,
            fine__target_scope='Class'  # Only class-specific fines
        ).select_related('fine', 'fine__class_section')
        
        removed_count = 0
        for fs in unpaid_fine_students:
            # If fine's class doesn't match student's current class, remove the FineStudent record
            if fs.fine.class_section != student.class_section:
                logger.info(f"Removing irrelevant fine {fs.fine.id} from student {student.admission_number} after promotion")
                fs.delete()
                removed_count += 1
        
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} irrelevant fine records for student {student.admission_number}")
            # Update student's due amount after cleanup
            student.update_due_amount()
        
        return removed_count
        
    except Exception as e:
        logger.error(f"Error cleaning up fines for student {student.admission_number}: {str(e)}")
        return 0

def apply_new_class_fines_after_promotion(student):
    """
    Apply any existing class-specific fines to a student after they are promoted to a new class.
    """
    try:
        from fines.models import Fine
        
        # Get all active class-specific fines for the student's new class
        class_fines = Fine.objects.filter(
            target_scope='Class',
            class_section=student.class_section,
            is_active=True
        )
        
        added_count = 0
        for fine in class_fines:
            # Check if student already has this fine
            if not FineStudent.objects.filter(fine=fine, student=student).exists():
                # Add the fine to this student
                FineStudent.objects.create(fine=fine, student=student)
                logger.info(f"Applied existing class fine {fine.id} to promoted student {student.admission_number}")
                added_count += 1
        
        if added_count > 0:
            logger.info(f"Applied {added_count} new class fines to student {student.admission_number}")
            # Update student's due amount after adding new fines
            student.update_due_amount()
        
        return added_count
        
    except Exception as e:
        logger.error(f"Error applying new class fines for student {student.admission_number}: {str(e)}")
        return 0

def handle_student_promotion(student, old_class_section=None):
    """
    Complete handler for student promotion - cleans up old fines and applies new ones.
    """
    logger.info(f"Handling promotion for student {student.admission_number} to class {student.class_section}")
    
    removed_count = cleanup_irrelevant_fines_after_promotion(student)
    added_count = apply_new_class_fines_after_promotion(student)
    
    return {
        'removed_fines': removed_count,
        'added_fines': added_count
    }