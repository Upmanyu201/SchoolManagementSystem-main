from django.core.cache import cache
from django.db import transaction
from django.db.models import Q, Count, Sum, Prefetch
from django.utils import timezone
from decimal import Decimal
from typing import Dict, List, Optional, Any
import logging

from .models import Student
from core.security_utils import sanitize_input, log_security_event
from core.cache_utils import sanitize_cache_key, safe_cache_set, safe_cache_get

logger = logging.getLogger(__name__)


class StudentService:
    """Optimized service layer for student operations"""
    
    @staticmethod
    def get_student_list_optimized(user, search_query: Optional[str] = None, 
                                 class_filter: Optional[int] = None) -> List[Student]:
        """
        Get optimized student list with minimal database queries
        """
        cache_key = sanitize_cache_key(f"students_list_{user.id}_{search_query or 'all'}_{class_filter or 'all'}")
        students = safe_cache_get(cache, cache_key)
        
        if students is None:
            queryset = Student.objects.get_list_optimized()
            
            # Apply filters
            if search_query:
                clean_query = sanitize_input(search_query)
                students = queryset.filter(
                    Q(first_name__icontains=clean_query) |
                    Q(last_name__icontains=clean_query) |
                    Q(admission_number__icontains=clean_query) |
                    Q(mobile_number__icontains=clean_query)
                )
            else:
                students = queryset
            
            if class_filter:
                students = students.filter(class_section_id=class_filter)
            
            # Convert to list for caching
            students = list(students)
            
            # Cache for 5 minutes
            safe_cache_set(cache, cache_key, students, 300)
        
        return students
    
    @staticmethod
    def create_student_optimized(validated_data: Dict, user) -> Student:
        """
        Create student with optimized operations and proper error handling
        """
        try:
            with transaction.atomic():
                # Ensure status is ACTIVE by default
                if 'status' not in validated_data or not validated_data['status']:
                    validated_data['status'] = 'ACTIVE'
                
                # Create student
                student = Student.objects.create(**validated_data)
                
                # Log creation
                log_security_event(
                    user,
                    'student_created',
                    f'Student {student.admission_number} created successfully'
                )
                
                # Clear relevant caches
                StudentService._clear_student_caches(user.id)
                cache.clear()  # Clear all caches to ensure new student appears
                return student
                
        except Exception as e:
            logger.error(f"Error creating student: {sanitize_input(str(e))}")
            raise
    
    @staticmethod
    def update_student_optimized(student: Student, validated_data: Dict, user) -> Student:
        """
        Update student with optimized operations and safe file handling
        """
        try:
            with transaction.atomic():
                # Handle file fields safely
                old_image = student.student_image
                
                # Update fields
                for field, value in validated_data.items():
                    setattr(student, field, value)
                
                student.save()
                
                # Clean up old image file if replaced
                if 'student_image' in validated_data and old_image and old_image != student.student_image:
                    try:
                        if old_image.storage.exists(old_image.name):
                            old_image.delete(save=False)
                    except Exception as file_error:
                        logger.warning(f"Could not delete old image file: {file_error}")
                
                # Log update
                log_security_event(
                    user,
                    'student_updated',
                    f'Student {student.admission_number} updated'
                )
                
                # Clear caches
                student.invalidate_cache()
                StudentService._clear_student_caches(user.id)
                
                return student
                
        except Exception as e:
            logger.error(f"Error updating student {student.id}: {sanitize_input(str(e))}")
            raise
    
    @staticmethod
    def delete_student_safe(student: Student, user) -> bool:
        """
        Safely delete student with dependency checks
        """
        try:
            # Check for related records
            has_fees = hasattr(student, 'fee_deposits') and student.fee_deposits.exists()
            has_attendance = False
            
            try:
                from attendance.models import Attendance
                has_attendance = Attendance.objects.filter(student=student).exists()
            except ImportError:
                pass
            
            if has_fees or has_attendance:
                return False  # Cannot delete - has related records
            
            with transaction.atomic():
                admission_number = student.admission_number
                student_name = f"{student.first_name} {student.last_name}"
                
                # Log deletion
                log_security_event(
                    user,
                    'student_deleted',
                    f'Student {admission_number} ({student_name}) deleted'
                )
                
                # Clear caches before deletion
                student.invalidate_cache()
                StudentService._clear_student_caches(user.id)
                
                student.delete()
                
                return True
                
        except Exception as e:
            logger.error(f"Error deleting student {student.id}: {sanitize_input(str(e))}")
            raise
    
    @staticmethod
    def get_dashboard_stats() -> Dict[str, Any]:
        """
        Get optimized dashboard statistics with safe field access
        """
        cache_key = sanitize_cache_key("student_dashboard_stats")
        stats = safe_cache_get(cache, cache_key)
        
        if stats is None:
            try:
                # Check if due_amount field exists
                student_fields = [f.name for f in Student._meta.get_fields()]
                has_due_amount = 'due_amount' in student_fields
                
                # Single query with aggregations
                if has_due_amount:
                    base_stats = Student.objects.aggregate(
                        total_students=Count('id'),
                        total_due=Sum('due_amount')
                    )
                    total_due = base_stats['total_due'] or Decimal('0')
                else:
                    base_stats = Student.objects.aggregate(
                        total_students=Count('id')
                    )
                    total_due = Decimal('0')
                
                # Get class-wise distribution safely
                try:
                    class_distribution = Student.objects.select_related('class_section').values(
                        'class_section__class_name'
                    ).annotate(
                        count=Count('id')
                    ).order_by('class_section__class_name')
                    class_dist_list = list(class_distribution)
                except Exception:
                    class_dist_list = []
                
                stats = {
                    'total_students': base_stats['total_students'] or 0,
                    'total_due_amount': total_due,
                    'class_distribution': class_dist_list,
                    'last_updated': timezone.now().isoformat()
                }
                
                # Cache for 10 minutes
                safe_cache_set(cache, cache_key, stats, 600)
                
            except Exception as e:
                logger.error(f"Error getting dashboard stats: {sanitize_input(str(e))}")
                # Return minimal stats
                stats = {
                    'total_students': Student.objects.count(),
                    'total_due_amount': Decimal('0'),
                    'class_distribution': [],
                    'last_updated': timezone.now().isoformat()
                }
        
        return stats
    
    @staticmethod
    def search_students_advanced(query: str, filters: Dict = None) -> List[Student]:
        """
        Advanced student search with multiple criteria
        """
        if not query or len(query.strip()) < 2:
            return []
        
        clean_query = sanitize_input(query.strip())
        cache_key = f"student_search_{hash(clean_query)}_{hash(str(filters or {}))}"
        
        results = cache.get(cache_key)
        if results is None:
            # Build search query
            search_q = Q(first_name__icontains=clean_query) | \
                      Q(last_name__icontains=clean_query) | \
                      Q(admission_number__icontains=clean_query) | \
                      Q(mobile_number__icontains=clean_query) | \
                      Q(email__icontains=clean_query)
            
            queryset = Student.objects.select_related('class_section').filter(search_q)
            
            # Apply additional filters
            if filters:
                if filters.get('class_id'):
                    queryset = queryset.filter(class_section_id=filters['class_id'])
                if filters.get('gender'):
                    queryset = queryset.filter(gender=filters['gender'])
                if filters.get('has_dues'):
                    queryset = queryset.filter(due_amount__gt=0)
            
            # Limit results and optimize fields
            results = list(queryset.only(
                'id', 'admission_number', 'first_name', 'last_name',
                'mobile_number', 'email', 'class_section__class_name',
                'class_section__section_name'
            )[:20])
            
            # Cache for 5 minutes
            cache.set(cache_key, results, 300)
        
        return results
    
    @staticmethod
    def get_student_financial_summary(student: Student) -> Dict[str, Any]:
        """
        Get comprehensive financial summary for a student
        """
        cache_key = f"student_financial_{student.id}"
        summary = cache.get(cache_key)
        
        if summary is None:
            # Get all financial data in optimized queries
            fee_stats = student.fee_deposits.aggregate(
                total_paid=Sum('paid_amount'),
                payment_count=Count('id')
            )
            
            # Get unpaid fines
            unpaid_fines = student.unpaid_fines_total
            
            # Calculate totals
            total_paid = fee_stats['total_paid'] or Decimal('0')
            carry_forward = student.due_amount or Decimal('0')
            current_dues = Decimal('7000.00')  # Should come from fee structure
            total_outstanding = carry_forward + current_dues + unpaid_fines - total_paid
            
            # Get last payment details
            last_payment = student.get_last_payment()
            
            summary = {
                'carry_forward': float(carry_forward),
                'current_session_dues': float(current_dues),
                'total_paid': float(total_paid),
                'unpaid_fines': float(unpaid_fines),
                'total_outstanding': float(max(total_outstanding, Decimal('0'))),
                'payment_count': fee_stats['payment_count'] or 0,
                'last_payment': last_payment,
                'payment_status': 'paid' if total_outstanding <= 0 else 'pending'
            }
            
            # Cache for 15 minutes
            cache.set(cache_key, summary, 900)
        
        return summary
    
    @staticmethod
    def bulk_update_due_amounts(student_ids: List[int], amount: Decimal, user) -> int:
        """
        Bulk update due amounts for multiple students
        """
        try:
            with transaction.atomic():
                updated_count = Student.objects.filter(
                    id__in=student_ids
                ).update(due_amount=amount)
                
                # Log bulk update
                log_security_event(
                    user,
                    'bulk_due_update',
                    f'Updated due amounts for {updated_count} students to {amount}'
                )
                
                # Clear caches for affected students
                for student_id in student_ids:
                    cache.delete_many([
                        f"student_financial_{student_id}",
                        f"financial_summary_{student_id}"
                    ])
                
                # Clear list caches
                StudentService._clear_student_caches(user.id)
                
                return updated_count
                
        except Exception as e:
            logger.error(f"Error in bulk update: {sanitize_input(str(e))}")
            raise
    
    @staticmethod
    def get_students_with_dues(min_amount: Decimal = Decimal('0')) -> List[Student]:
        """
        Get students with outstanding dues
        """
        cache_key = f"students_with_dues_{min_amount}"
        students = cache.get(cache_key)
        
        if students is None:
            students = list(
                Student.objects.select_related('class_section')
                .filter(due_amount__gt=min_amount)
                .only(
                    'id', 'admission_number', 'first_name', 'last_name',
                    'mobile_number', 'due_amount', 'class_section__class_name'
                )
                .order_by('-due_amount')
            )
            
            # Cache for 30 minutes
            cache.set(cache_key, students, 1800)
        
        return students
    
    @staticmethod
    def _clear_student_caches(user_id: int):
        """
        Clear student-related caches
        """
        cache_patterns = [
            f"students_list_{user_id}*",
            "student_dashboard_stats",
            "students_with_dues_*"
        ]
        
        # Note: Django cache doesn't support pattern deletion
        # In production, consider using Redis with pattern deletion
        cache.delete_many([
            f"students_list_{user_id}",
            "student_dashboard_stats"
        ])


class StudentDashboardService:
    """Service for student dashboard operations"""
    
    @staticmethod
    def get_complete_dashboard_data(student: Student) -> Dict[str, Any]:
        """
        Get all dashboard data in optimized queries
        """
        cache_key = f"complete_dashboard_{student.id}"
        data = cache.get(cache_key)
        
        if data is None:
            # Get all data with minimal queries
            data = {
                'profile': {
                    'admission_number': student.admission_number,
                    'name': f"{student.first_name} {student.last_name}",
                    'class': student.class_section.class_name if student.class_section else 'N/A',
                    'section': student.class_section.section_name if student.class_section else 'N/A',
                    'photo': student.get_image_url(),
                    'mobile': student.mobile_number,
                    'email': student.email
                },
                'financial': student.financial_summary,
                'academic': {
                    'attendance_percentage': student.attendance_percentage,
                    'class_info': f"{student.class_section}" if student.class_section else 'N/A'
                },
                'recent_activities': student.recent_activities[:10]
            }
            
            # Cache for 10 minutes
            cache.set(cache_key, data, 600)
        
        return data
    
    @staticmethod
    def get_student_timeline(student: Student, days: int = 30) -> List[Dict]:
        """
        Get chronological timeline of student activities
        """
        cache_key = f"student_timeline_{student.id}_{days}"
        timeline = cache.get(cache_key)
        
        if timeline is None:
            timeline = []
            cutoff_date = timezone.now().date() - timezone.timedelta(days=days)
            
            # Fee payments
            payments = student.fee_deposits.filter(
                deposit_date__gte=cutoff_date
            ).only('deposit_date', 'paid_amount', 'receipt_no')
            
            for payment in payments:
                timeline.append({
                    'type': 'payment',
                    'date': payment.deposit_date,
                    'title': 'Fee Payment',
                    'description': f'Paid ₹{payment.paid_amount}',
                    'icon': 'fas fa-credit-card',
                    'color': 'success'
                })
            
            # Sort by date
            timeline.sort(key=lambda x: x['date'], reverse=True)
            
            # Cache for 1 hour
            cache.set(cache_key, timeline, 3600)
        
        return timeline


class StudentExportService:
    """Service for student data export operations"""
    
    @staticmethod
    def prepare_export_data(students: List[Student], include_financial: bool = False) -> tuple:
        """
        Prepare optimized data for export
        """
        headers = [
            'Admission Number', 'First Name', 'Last Name', 'Class', 'Section',
            'Mobile Number', 'Email', 'Date of Birth', 'Date of Admission'
        ]
        
        if include_financial:
            headers.extend(['Due Amount', 'Total Paid', 'Outstanding'])
        
        data = []
        for student in students:
            row = [
                student.admission_number,
                student.first_name,
                student.last_name,
                student.class_section.class_name if student.class_section else 'N/A',
                student.class_section.section_name if student.class_section else 'N/A',
                student.mobile_number,
                student.email,
                student.date_of_birth.strftime('%Y-%m-%d') if student.date_of_birth else '',
                student.date_of_admission.strftime('%Y-%m-%d') if student.date_of_admission else ''
            ]
            
            if include_financial:
                financial = student.financial_summary
                row.extend([
                    str(student.due_amount or 0),
                    str(financial.get('paid_amount', 0)),
                    str(financial.get('total_outstanding', 0))
                ])
            
            data.append(row)
        
        return data, headers