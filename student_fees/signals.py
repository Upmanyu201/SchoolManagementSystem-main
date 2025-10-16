"""
Signals for handling student fee and fine updates
"""
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from students.models import Student
import logging

logger = logging.getLogger(__name__)

@receiver(pre_save, sender=Student)
def track_class_change(sender, instance, **kwargs):
    """Track when a student's class is about to change"""
    if instance.pk:  # Only for existing students
        try:
            old_instance = Student.objects.get(pk=instance.pk)
            instance._old_class_section = old_instance.class_section
        except Student.DoesNotExist:
            instance._old_class_section = None
    else:
        instance._old_class_section = None

@receiver(post_save, sender=Student)
def handle_class_change(sender, instance, created, **kwargs):
    """Handle fine cleanup and application when student class changes"""
    if not created and hasattr(instance, '_old_class_section'):
        old_class = instance._old_class_section
        new_class = instance.class_section
        
        # If class actually changed
        if old_class != new_class:
            logger.info(f"Student {instance.admission_number} class changed from {old_class} to {new_class}")
            
            try:
                from .promotion_utils import handle_student_promotion
                result = handle_student_promotion(instance, old_class)
                logger.info(f"Promotion handled for {instance.admission_number}: {result}")
            except Exception as e:
                logger.error(f"Error handling promotion for {instance.admission_number}: {str(e)}")