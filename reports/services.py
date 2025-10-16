# reports/services.py - Enterprise-grade service layer
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timedelta
import json

from django.db.models import Q, Sum, Count, Avg, F, Case, When, Value
from django.core.cache import cache
from django.utils import timezone
from django.contrib.auth.models import User
from pydantic import BaseModel, Field, validator

from students.models import Student
from fees.models import FeesType
from student_fees.models import FeeDeposit
from fines.models import Fine, FineStudent
from attendance.models import Attendance
from subjects.models import ClassSection

# Centralized fee service integration
try:
    from core.fee_management import fee_service
    FEE_SERVICE_AVAILABLE = True
except ImportError:
    fee_service = None
    FEE_SERVICE_AVAILABLE = False


# Pydantic models for validation
class ReportFilters(BaseModel):
    """Validated report filters"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    class_id: Optional[int] = None
    student_ids: Optional[List[int]] = None
    report_type: str = Field(..., pattern=r'^[a-zA-Z_]+$')
    
    @validator('start_date', 'end_date')
    def validate_dates(cls, v):
        if v and v > timezone.now():
            raise ValueError('Date cannot be in the future')
        return v


class AnalyticsFilters(BaseModel):
    """Validated analytics filters"""
    period: str = Field('month', pattern=r'^(day|week|month|quarter|year)$')
    class_ids: Optional[List[int]] = None
    metric_types: List[str] = Field(default=['fees', 'attendance', 'performance'])


@dataclass
class ReportResult:
    """Structured report result"""
    data: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    totals: Dict[str, Decimal]
    generated_at: datetime
    cache_key: Optional[str] = None


class ReportSecurityService:
    """Security service for reports"""
    
    @staticmethod
    def validate_user_permissions(user: User, report_type: str) -> bool:
        """Validate user has permission for report type"""
        permission_map = {
            'fees_report': 'reports.view_fees',
            'attendance_report': 'reports.view_attendance',
            'student_report': 'reports.view_students',
            'analytics_dashboard': 'reports.view_analytics'
        }
        
        required_permission = permission_map.get(report_type)
        if not required_permission:
            return False
            
        return user.has_perm(required_permission)
    
    @staticmethod
    def sanitize_filters(filters: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize and validate filter inputs"""
        # Remove any potentially dangerous keys
        dangerous_keys = ['__', 'sql', 'query', 'raw']
        cleaned_filters = {
            k: v for k, v in filters.items() 
            if not any(danger in str(k).lower() for danger in dangerous_keys)
        }
        
        # Validate integer IDs
        for key in ['class_id', 'student_id', 'section_id']:
            if key in cleaned_filters:
                try:
                    cleaned_filters[key] = int(cleaned_filters[key])
                except (ValueError, TypeError):
                    del cleaned_filters[key]
        
        return cleaned_filters


class ReportCacheService:
    """Caching service for reports"""
    
    @staticmethod
    def get_cache_key(report_type: str, filters: Dict[str, Any], user_id: int) -> str:
        """Generate cache key for report"""
        filter_hash = hash(json.dumps(filters, sort_keys=True, default=str))
        return f"report:{report_type}:{user_id}:{filter_hash}"
    
    @staticmethod
    async def get_cached_report(cache_key: str) -> Optional[ReportResult]:
        """Get cached report result"""
        cached_data = cache.get(cache_key)
        if cached_data:
            return ReportResult(**cached_data)
        return None
    
    @staticmethod
    async def cache_report(cache_key: str, result: ReportResult, timeout: int = 300):
        """Cache report result"""
        cache_data = {
            'data': result.data,
            'metadata': result.metadata,
            'totals': {k: float(v) for k, v in result.totals.items()},
            'generated_at': result.generated_at.isoformat(),
            'cache_key': cache_key
        }
        cache.set(cache_key, cache_data, timeout)


class AdvancedReportService:
    """Enterprise-grade report service"""
    
    def __init__(self):
        self.security = ReportSecurityService()
        self.cache = ReportCacheService()
    
    async def generate_comprehensive_fees_report(
        self, 
        filters: ReportFilters, 
        user: User
    ) -> ReportResult:
        """Generate comprehensive fees report with security and caching"""
        
        # Security validation
        if not self.security.validate_user_permissions(user, 'fees_report'):
            raise PermissionError("Insufficient permissions for fees report")
        
        # Check cache first
        cache_key = self.cache.get_cache_key('fees_comprehensive', filters.dict(), user.id)
        cached_result = await self.cache.get_cached_report(cache_key)
        if cached_result:
            return cached_result
        
        # Build secure query
        students_query = Q()
        if filters.class_id:
            students_query &= Q(class_section_id=filters.class_id)
        if filters.student_ids:
            students_query &= Q(id__in=filters.student_ids)
        
        students = Student.objects.filter(students_query).select_related(
            'class_section'
        ).prefetch_related(
            'feedeposit_set',
            'finestudent_set__fine'
        )
        
        # Process data asynchronously
        report_data = []
        totals = {
            'current_fees': Decimal('0'),
            'current_paid': Decimal('0'),
            'current_discount': Decimal('0'),
            'cf_due': Decimal('0'),
            'fine_unpaid': Decimal('0'),
            'final_due': Decimal('0')
        }
        
        async for student in students.aiterator():
            student_data = await self._calculate_student_fees(student)
            if student_data:
                report_data.append(student_data)
                for key in totals:
                    totals[key] += student_data.get(key, Decimal('0'))
        
        result = ReportResult(
            data=report_data,
            metadata={
                'report_type': 'comprehensive_fees',
                'filters': filters.dict(),
                'total_students': len(report_data),
                'generated_by': user.username
            },
            totals=totals,
            generated_at=timezone.now()
        )
        
        # Cache the result
        await self.cache.cache_report(cache_key, result)
        
        return result
    
    async def _calculate_student_fees(self, student: Student) -> Optional[Dict[str, Any]]:
        """Calculate comprehensive fee data for a student using centralized service"""
        try:
            # Use centralized fee service if available
            if FEE_SERVICE_AVAILABLE and fee_service:
                try:
                    fee_breakdown = fee_service.get_payment_breakdown(student)
                    if fee_breakdown:
                        return {
                            'student_id': student.id,
                            'name': student.get_full_display_name(),
                            'class_name': f"{student.class_section.class_name} - {student.class_section.section_name}" if student.class_section else 'Unknown',
                            'current_fees': fee_breakdown.get('total_fees', Decimal('0')),
                            'current_paid': fee_breakdown.get('total_paid', Decimal('0')),
                            'current_discount': fee_breakdown.get('total_discount', Decimal('0')),
                            'cf_due': fee_breakdown.get('carry_forward', Decimal('0')),
                            'fine_unpaid': fee_breakdown.get('fine_amount', Decimal('0')),
                            'fine_paid': Decimal('0'),  # Handled in service
                            'final_due': fee_breakdown.get('total_due', Decimal('0')),
                            'service_calculated': True
                        }
                except Exception as e:
                    print(f"Fee service error for student {student.id}: {e}")
            
            # Fallback to original calculation
            class_name = student.class_section.class_name if student.class_section else ''
            
            applicable_fees = await FeesType.objects.filter(
                Q(class_name__isnull=True) | Q(class_name__iexact=class_name)
            ).exclude(group_type="Transport").aaggregate(
                total=Sum('amount')
            )
            
            current_fees = applicable_fees.get('total') or Decimal('0')
            
            # Get payments (exclude fine payments)
            payments = await FeeDeposit.objects.filter(
                student=student
            ).exclude(note__icontains="Fine Payment").aaggregate(
                paid=Sum('paid_amount'),
                discount=Sum('discount')
            )
            
            current_paid = payments.get('paid') or Decimal('0')
            current_discount = payments.get('discount') or Decimal('0')
            
            # Get carry forward
            cf_due = student.due_amount or Decimal('0')
            
            # Get fines
            fines = await FineStudent.objects.filter(
                student=student
            ).select_related('fine').aaggregate(
                unpaid=Sum('fine__amount', filter=Q(is_paid=False)),
                paid=Sum('fine__amount', filter=Q(is_paid=True))
            )
            
            fine_unpaid = fines.get('unpaid') or Decimal('0')
            fine_paid = fines.get('paid') or Decimal('0')
            
            # Calculate final due
            final_due = max(
                current_fees - current_paid - current_discount + cf_due + fine_unpaid,
                Decimal('0')
            )
            
            # Only return if there's any fee activity
            if any([current_fees, current_paid, cf_due, fine_unpaid, fine_paid]):
                return {
                    'student_id': student.id,
                    'name': student.get_full_display_name(),
                    'class_name': f"{student.class_section.class_name} - {student.class_section.section_name}" if student.class_section else 'Unknown',
                    'current_fees': current_fees,
                    'current_paid': current_paid,
                    'current_discount': current_discount,
                    'cf_due': cf_due,
                    'fine_unpaid': fine_unpaid,
                    'fine_paid': fine_paid,
                    'final_due': final_due,
                    'service_calculated': False
                }
            
            return None
            
        except Exception as e:
            # Log error but don't break the entire report
            print(f"Error calculating fees for student {student.id}: {e}")
            return None
    
    async def generate_analytics_dashboard(
        self, 
        filters: AnalyticsFilters, 
        user: User
    ) -> Dict[str, Any]:
        """Generate real-time analytics dashboard data"""
        
        if not self.security.validate_user_permissions(user, 'analytics_dashboard'):
            raise PermissionError("Insufficient permissions for analytics dashboard")
        
        # Parallel data fetching for performance
        tasks = []
        
        if 'fees' in filters.metric_types:
            tasks.append(self._get_fee_analytics(filters))
        if 'attendance' in filters.metric_types:
            tasks.append(self._get_attendance_analytics(filters))
        if 'performance' in filters.metric_types:
            tasks.append(self._get_performance_analytics(filters))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        dashboard_data = {
            'timestamp': timezone.now().isoformat(),
            'period': filters.period,
            'metrics': {}
        }
        
        for i, result in enumerate(results):
            if not isinstance(result, Exception):
                metric_type = filters.metric_types[i]
                dashboard_data['metrics'][metric_type] = result
        
        return dashboard_data
    
    async def _get_fee_analytics(self, filters: AnalyticsFilters) -> Dict[str, Any]:
        """Get fee collection analytics"""
        # Implementation for fee analytics
        return {
            'total_collected': 0,
            'collection_rate': 0,
            'pending_amount': 0,
            'trend': []
        }
    
    async def _get_attendance_analytics(self, filters: AnalyticsFilters) -> Dict[str, Any]:
        """Get attendance analytics"""
        # Implementation for attendance analytics
        return {
            'average_attendance': 0,
            'trend': [],
            'class_wise': {}
        }
    
    async def _get_performance_analytics(self, filters: AnalyticsFilters) -> Dict[str, Any]:
        """Get performance analytics"""
        # Implementation for performance analytics
        return {
            'average_grade': 0,
            'top_performers': [],
            'improvement_needed': []
        }


class ReportExportService:
    """Modern export service with multiple formats"""
    
    @staticmethod
    async def export_to_excel(data: List[Dict], filename: str) -> str:
        """Export data to Excel with professional formatting"""
        import pandas as pd
        from openpyxl.styles import Font, PatternFill, Alignment
        
        df = pd.DataFrame(data)
        
        # Create Excel file with formatting
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Report', index=False)
            
            # Get workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Report']
            
            # Apply formatting
            header_font = Font(bold=True, color='FFFFFF')
            header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
            
            for cell in worksheet[1]:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal='center')
        
        return filename
    
    @staticmethod
    async def export_to_pdf(data: List[Dict], template_name: str) -> str:
        """Export data to PDF using modern template"""
        from weasyprint import HTML, CSS
        from django.template.loader import render_to_string
        
        html_content = render_to_string(template_name, {'data': data})
        
        # Modern CSS styling
        css_content = CSS(string="""
            @page { size: A4; margin: 1cm; }
            body { font-family: 'Segoe UI', sans-serif; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; }
            .table { width: 100%; border-collapse: collapse; }
            .table th, .table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            .table th { background-color: #f8f9fa; font-weight: bold; }
        """)
        
        filename = f"report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        HTML(string=html_content).write_pdf(filename, stylesheets=[css_content])
        
        return filename


# Service instances
report_service = AdvancedReportService()
export_service = ReportExportService()