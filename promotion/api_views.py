# promotion/api_views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from .models import PromotionRule, StudentPromotion
from .serializers import PromotionRuleSerializer, StudentPromotionSerializer
from students.models import Student
from subjects.models import ClassSection
from users.decorators import module_required
from django.utils.decorators import method_decorator

@method_decorator(module_required('promotion', 'view'), name='list')
@method_decorator(module_required('promotion', 'edit'), name='create')
class PromotionRuleViewSet(viewsets.ModelViewSet):
    queryset = PromotionRule.objects.select_related('from_class_section', 'to_class_section')
    serializer_class = PromotionRuleSerializer

@method_decorator(module_required('promotion', 'view'), name='list')
@method_decorator(module_required('promotion', 'edit'), name='create')
class StudentPromotionViewSet(viewsets.ModelViewSet):
    queryset = StudentPromotion.objects.select_related('student', 'from_class_section', 'to_class_section')
    serializer_class = StudentPromotionSerializer
    
    @action(detail=False, methods=['post'])
    def bulk_promote(self, request):
        """Bulk promote students"""
        try:
            from_class_id = request.data.get('from_class_id')
            to_class_id = request.data.get('to_class_id')
            student_ids = request.data.get('student_ids', [])
            academic_year = request.data.get('academic_year')
            
            if not all([from_class_id, to_class_id, student_ids, academic_year]):
                return Response({'error': 'Missing required fields'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            from_class = ClassSection.objects.get(id=from_class_id)
            to_class = ClassSection.objects.get(id=to_class_id)
            
            promoted_count = 0
            
            with transaction.atomic():
                for student_id in student_ids:
                    try:
                        student = Student.objects.get(id=student_id)
                        
                        # Create promotion record
                        StudentPromotion.objects.create(
                            student=student,
                            from_class_section=from_class,
                            to_class_section=to_class,
                            academic_year=academic_year,
                            promotion_date=request.data.get('promotion_date'),
                            remarks=request.data.get('remarks', '')
                        )
                        
                        # Update student's class
                        student.class_section = to_class
                        student.save()
                        
                        promoted_count += 1
                        
                    except Student.DoesNotExist:
                        continue
            
            return Response({
                'message': f'Successfully promoted {promoted_count} students',
                'promoted_count': promoted_count
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def eligible_students(self, request):
        """Get students eligible for promotion"""
        class_id = request.query_params.get('class_id')
        
        if not class_id:
            return Response({'error': 'Class ID is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        students = Student.objects.filter(class_section_id=class_id).select_related('class_section')
        
        student_data = []
        for student in students:
            student_data.append({
                'id': student.id,
                'name': f"{student.first_name} {student.last_name}",
                'admission_number': student.admission_number,
                'current_class': student.class_section.class_name if student.class_section else 'N/A'
            })
        
        return Response(student_data)