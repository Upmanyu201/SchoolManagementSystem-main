# attendance/api_views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Attendance
from .serializers import AttendanceSerializer
from students.models import Student
from subjects.models import ClassSection
from users.decorators import module_required
from django.utils.decorators import method_decorator

@method_decorator(module_required('attendance', 'view'), name='list')
@method_decorator(module_required('attendance', 'edit'), name='create')
class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.select_related('student', 'student__class_section')
    serializer_class = AttendanceSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        class_id = self.request.query_params.get('class_id')
        date = self.request.query_params.get('date')
        
        if class_id:
            queryset = queryset.filter(student__class_section_id=class_id)
        if date:
            queryset = queryset.filter(date=date)
            
        return queryset.order_by('-date', 'student__first_name')
    
    @action(detail=False, methods=['post'])
    def bulk_mark(self, request):
        """Bulk mark attendance for a class"""
        try:
            class_id = request.data.get('class_id')
            date = request.data.get('date')
            attendance_data = request.data.get('attendance', [])
            
            if not class_id or not date:
                return Response({'error': 'Class ID and date are required'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            # Delete existing attendance for this class and date
            Attendance.objects.filter(
                student__class_section_id=class_id,
                date=date
            ).delete()
            
            # Create new attendance records
            attendance_records = []
            for item in attendance_data:
                student = get_object_or_404(Student, id=item['student_id'])
                attendance_records.append(Attendance(
                    student=student,
                    date=date,
                    status=item['status']
                ))
            
            Attendance.objects.bulk_create(attendance_records)
            
            return Response({
                'message': f'Attendance marked for {len(attendance_records)} students',
                'count': len(attendance_records)
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def report(self, request):
        """Generate attendance report"""
        class_id = request.query_params.get('class_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        queryset = self.get_queryset()
        
        if start_date and end_date:
            queryset = queryset.filter(date__range=[start_date, end_date])
        
        # Calculate attendance percentage
        report_data = []
        students = Student.objects.filter(class_section_id=class_id) if class_id else Student.objects.all()
        
        for student in students:
            total = queryset.filter(student=student).count()
            present = queryset.filter(student=student, status='Present').count()
            percentage = (present / total * 100) if total > 0 else 0
            
            report_data.append({
                'student_id': student.id,
                'student_name': f"{student.first_name} {student.last_name}",
                'admission_number': student.admission_number,
                'total_days': total,
                'present_days': present,
                'absent_days': total - present,
                'percentage': round(percentage, 2)
            })
        
        return Response(report_data)