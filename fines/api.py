# fines/api.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Sum
from .models import Fine, FineType, FineStudent
from .serializers import FineSerializer, FineTypeSerializer, FineStudentSerializer
from students.models import Student
from users.decorators import module_required
from django.utils.decorators import method_decorator

@method_decorator(module_required('fines', 'view'), name='list')
@method_decorator(module_required('fines', 'edit'), name='create')
class FineViewSet(viewsets.ModelViewSet):
    queryset = Fine.objects.select_related('fine_type')
    serializer_class = FineSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        fine_type = self.request.query_params.get('fine_type')
        class_id = self.request.query_params.get('class_id')
        
        if fine_type:
            queryset = queryset.filter(fine_type_id=fine_type)
        if class_id:
            queryset = queryset.filter(class_section_id=class_id)
            
        return queryset.order_by('-created_at')

@method_decorator(module_required('fines', 'view'), name='list')
@method_decorator(module_required('fines', 'edit'), name='create')
class FineTypeViewSet(viewsets.ModelViewSet):
    queryset = FineType.objects.all()
    serializer_class = FineTypeSerializer

@method_decorator(module_required('fines', 'view'), name='list')
@method_decorator(module_required('fines', 'edit'), name='create')
class FineStudentViewSet(viewsets.ModelViewSet):
    queryset = FineStudent.objects.select_related('fine', 'student')
    serializer_class = FineStudentSerializer
    
    @action(detail=False, methods=['post'])
    def bulk_waive(self, request):
        """Bulk waive fines"""
        try:
            fine_ids = request.data.get('fine_ids', [])
            
            if not fine_ids:
                return Response({'error': 'No fine IDs provided'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            waived_count = FineStudent.objects.filter(
                id__in=fine_ids,
                is_paid=False
            ).update(is_waived=True)
            
            return Response({
                'message': f'Waived {waived_count} fines',
                'waived_count': waived_count
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def unpaid_summary(self, request):
        """Get unpaid fines summary"""
        unpaid_fines = self.get_queryset().filter(is_paid=False, is_waived=False)
        
        summary = {
            'total_unpaid': unpaid_fines.count(),
            'total_amount': unpaid_fines.aggregate(
                total=Sum('fine__amount')
            )['total'] or 0,
            'by_type': unpaid_fines.values('fine__fine_type__name').annotate(
                count=models.Count('id'),
                amount=Sum('fine__amount')
            )
        }
        
        return Response(summary)