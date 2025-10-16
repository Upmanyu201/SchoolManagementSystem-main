# fees/services.py
from django.db.models import Sum, Q
from django.core.cache import cache
from .models import FeesGroup, FeesType
from students.models import Student
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class FeeService:
    @staticmethod
    def get_applicable_fees(student):
        """Get applicable fees for a student"""
        cache_key = f"applicable_fees_{student.id}"
        fees = cache.get(cache_key)
        
        if not fees:
            # Get fees based on class
            class_fees = FeesType.objects.filter(
                Q(class_name=student.class_section.class_name) |
                Q(class_name__isnull=True)
            ).select_related('fee_group')
            
            # Get transport fees if applicable
            transport_fees = []
            try:
                from transport.models import TransportAssignment
                transport = TransportAssignment.objects.filter(student=student).first()
                if transport:
                    transport_fees = FeesType.objects.filter(
                        related_stoppage=transport.stoppage
                    ).select_related('fee_group')
            except ImportError:
                pass
            
            fees = {
                'class_fees': list(class_fees),
                'transport_fees': list(transport_fees)
            }
            cache.set(cache_key, fees, 1800)  # 30 minutes
        
        return fees
    
    @staticmethod
    def calculate_total_fees(student):
        """Calculate total applicable fees for student"""
        applicable_fees = FeeService.get_applicable_fees(student)
        
        total = Decimal('0')
        for fee in applicable_fees['class_fees']:
            total += fee.amount
        
        for fee in applicable_fees['transport_fees']:
            total += fee.amount
        
        return total
    
    @staticmethod
    def get_fee_structure_by_class(class_name):
        """Get fee structure for a specific class"""
        return FeesType.objects.filter(
            class_name=class_name
        ).select_related('fee_group').order_by('fee_group__fee_group')
    
    @staticmethod
    def bulk_create_fee_types(fee_types_data):
        """Bulk create fee types"""
        created_fees = []
        
        for fee_data in fee_types_data:
            try:
                fee_type = FeesType.objects.create(**fee_data)
                created_fees.append(fee_type)
            except Exception as e:
                logger.error(f"Error creating fee type: {e}")
                continue
        
        # Clear cache
        cache.delete_pattern('applicable_fees_*')
        
        return created_fees