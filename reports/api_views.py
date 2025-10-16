# reports/api_views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from students.models import Student
from student_fees.models import FeeDeposit
from fines.models import FineStudent
from attendance.models import Attendance
from .serializers import ReportDataSerializer
from users.decorators import module_required
from django.utils.decorators import method_decorator

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@module_required('reports', 'view')
def fees_report_api(request):
    """Generate fees report via API"""
    try:
        class_id = request.query_params.get('class_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Base queryset
        deposits = FeeDeposit.objects.select_related('student', 'fees_type')
        
        if class_id:
            deposits = deposits.filter(student__class_section_id=class_id)
        if start_date:
            deposits = deposits.filter(deposit_date__gte=start_date)
        if end_date:
            deposits = deposits.filter(deposit_date__lte=end_date)
        
        # Calculate summary
        summary = deposits.aggregate(
            total_amount=Sum('amount'),
            total_paid=Sum('paid_amount'),
            total_discount=Sum('discount'),
            total_records=Count('id')
        )
        
        # Get detailed data
        report_data = []
        for deposit in deposits[:100]:  # Limit for performance
            report_data.append({
                'student_name': f"{deposit.student.first_name} {deposit.student.last_name}",
                'admission_number': deposit.student.admission_number,
                'class_name': deposit.student.class_section.class_name if deposit.student.class_section else 'N/A',
                'fee_type': deposit.fees_type.group_type if deposit.fees_type else 'Other',
                'amount': float(deposit.amount),
                'paid_amount': float(deposit.paid_amount),
                'discount': float(deposit.discount or 0),
                'deposit_date': deposit.deposit_date,
                'receipt_no': deposit.receipt_no
            })
        
        return Response({
            'summary': summary,
            'data': report_data,
            'total_records': len(report_data)
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@module_required('reports', 'view')
def attendance_report_api(request):
    """Generate attendance report via API"""
    try:
        class_id = request.query_params.get('class_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Default to last 30 days if no dates provided
        if not start_date:
            start_date = timezone.now().date() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now().date()
        
        # Get students
        students = Student.objects.all()
        if class_id:
            students = students.filter(class_section_id=class_id)
        
        report_data = []
        for student in students[:50]:  # Limit for performance
            attendance_records = Attendance.objects.filter(
                student=student,
                date__range=[start_date, end_date]
            )
            
            total_days = attendance_records.count()
            present_days = attendance_records.filter(status='Present').count()
            percentage = (present_days / total_days * 100) if total_days > 0 else 0
            
            report_data.append({
                'student_name': f"{student.first_name} {student.last_name}",
                'admission_number': student.admission_number,
                'class_name': student.class_section.class_name if student.class_section else 'N/A',
                'total_days': total_days,
                'present_days': present_days,
                'absent_days': total_days - present_days,
                'percentage': round(percentage, 2)
            })
        
        return Response({
            'data': report_data,
            'period': {'start_date': start_date, 'end_date': end_date},
            'total_students': len(report_data)
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@module_required('reports', 'view')
def dashboard_summary_api(request):
    """Get dashboard summary data"""
    try:
        # Get current month data
        current_month = timezone.now().replace(day=1).date()
        
        summary = {
            'students': {
                'total': Student.objects.count(),
                'new_this_month': Student.objects.filter(
                    date_of_admission__gte=current_month
                ).count()
            },
            'fees': {
                'collected_this_month': FeeDeposit.objects.filter(
                    deposit_date__gte=current_month
                ).aggregate(total=Sum('paid_amount'))['total'] or 0,
                'pending_amount': Student.objects.aggregate(
                    total=Sum('due_amount')
                )['total'] or 0
            },
            'fines': {
                'unpaid_count': FineStudent.objects.filter(
                    is_paid=False, is_waived=False
                ).count(),
                'unpaid_amount': FineStudent.objects.filter(
                    is_paid=False, is_waived=False
                ).aggregate(total=Sum('fine__amount'))['total'] or 0
            }
        }
        
        return Response(summary)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)