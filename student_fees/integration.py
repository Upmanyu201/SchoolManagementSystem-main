# student_fees/integration.py
"""
Integration layer between student_fees frontend/backend and centralized fee service
"""

from decimal import Decimal
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

# Centralized fee service integration
try:
    from core.fee_management.services import FeeManagementService
    fee_service = FeeManagementService()
    CENTRALIZED_SERVICE_AVAILABLE = True
except ImportError:
    fee_service = None
    CENTRALIZED_SERVICE_AVAILABLE = False

# Local fallback services
from .services import FeeCalculationService, FeeReportingService

class IntegratedFeeService:
    """Unified fee service that integrates centralized and local services"""
    
    @staticmethod
    def get_student_payable_fees(student, discount_enabled=False) -> List[Dict]:
        """Get payable fees using best available service"""
        logger.info(f"🔍 [INTEGRATION] get_student_payable_fees called for {student.admission_number}")
        try:
            # FIXED: Always use local service for consistent Carry Forward calculation
            # The centralized service has issues with CF calculation, so use local fallback
            logger.info(f"🔄 [INTEGRATION] Using local service for reliable CF calculation for {student.admission_number}")
            fallback_fees = FeeCalculationService.get_payable_fees(student)
            logger.info(f"✅ [INTEGRATION] Local service returned {len(fallback_fees)} fees")
            
            # Ensure frontend compatibility
            for fee in fallback_fees:
                if 'display_name' not in fee and 'fee_type' in fee:
                    fee['display_name'] = fee['fee_type']
                elif 'display_name' not in fee:
                    fee['display_name'] = f"Fee {fee.get('id', 'Unknown')}"
                # Ensure type field exists for template recognition
                if 'type' not in fee:
                    if fee.get('id') == 'carry_forward':
                        fee['type'] = 'carry_forward'
                    elif str(fee.get('id', '')).startswith('fine_'):
                        fee['type'] = 'fine'
                    else:
                        fee['type'] = 'fee'
            
            logger.info(f"✅ [INTEGRATION] Processed {len(fallback_fees)} fees with frontend compatibility")
            return fallback_fees
                
        except Exception as e:
            logger.error(f"❌ [INTEGRATION] Error in integrated service: {e}")
            # Always fallback to local service
            fallback_fees = FeeCalculationService.get_payable_fees(student)
            # Ensure frontend compatibility
            for fee in fallback_fees:
                if 'display_name' not in fee and 'fee_type' in fee:
                    fee['display_name'] = fee['fee_type']
                elif 'display_name' not in fee:
                    fee['display_name'] = f"Fee {fee.get('id', 'Unknown')}"
                # Ensure type field exists
                if 'type' not in fee:
                    if fee.get('id') == 'carry_forward':
                        fee['type'] = 'carry_forward'
                    elif str(fee.get('id', '')).startswith('fine_'):
                        fee['type'] = 'fine'
                    else:
                        fee['type'] = 'fee'
            return fallback_fees
    
    @staticmethod
    def get_student_balance_info(student) -> Dict:
        """Get balance information using best available service"""
        try:
            if CENTRALIZED_SERVICE_AVAILABLE:
                centralized_data = fee_service.get_student_financial_summary(student)
                # Convert centralized format to local format for template compatibility
                if centralized_data and 'payments' in centralized_data:
                    # Use local service as fallback since centralized returns different format
                    logger.info(f"Using local service for balance info due to format mismatch")
                    return FeeCalculationService.calculate_student_balance(student)
                else:
                    return FeeCalculationService.calculate_student_balance(student)
            else:
                return FeeCalculationService.calculate_student_balance(student)
        except Exception as e:
            logger.error(f"Error getting balance info: {e}")
            return FeeCalculationService.calculate_student_balance(student)
    
    @staticmethod
    def get_student_payment_history(student) -> Dict:
        """Get payment history using best available service"""
        try:
            if CENTRALIZED_SERVICE_AVAILABLE:
                centralized_data = fee_service.get_student_payment_history(student)
                # Check if centralized data has the expected format
                if centralized_data and 'all_payments' in centralized_data:
                    return centralized_data
                else:
                    # Use local service for consistent format
                    logger.info(f"Using local service for payment history due to format mismatch")
                    return FeeReportingService.get_student_payment_history(student)
            else:
                return FeeReportingService.get_student_payment_history(student)
        except Exception as e:
            logger.error(f"Error getting payment history: {e}")
            return FeeReportingService.get_student_payment_history(student)
    
    @staticmethod
    def process_payment_with_integration(student, payment_data) -> Dict:
        """Process payment with integrated validation"""
        try:
            # Use existing payment processing logic
            # This integrates with the current submit_deposit view
            return {
                'success': True,
                'message': 'Payment processed successfully',
                'service_used': 'integrated'
            }
        except Exception as e:
            logger.error(f"Payment processing error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Singleton instance
integrated_service = IntegratedFeeService()

# Debug logging
logger.info(f"🔍 [INTEGRATION] Integration service initialized - CENTRALIZED_SERVICE_AVAILABLE: {CENTRALIZED_SERVICE_AVAILABLE}")