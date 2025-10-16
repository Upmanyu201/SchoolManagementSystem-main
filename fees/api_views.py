# fees/api_views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import FeesGroup, FeesType
from .serializers import FeesGroupSerializer, FeesTypeSerializer
from users.decorators import module_required
from django.utils.decorators import method_decorator

@method_decorator(module_required('fees', 'view'), name='list')
@method_decorator(module_required('fees', 'edit'), name='create')
class FeesGroupViewSet(viewsets.ModelViewSet):
    queryset = FeesGroup.objects.select_related('related_class_section', 'related_stoppage')
    serializer_class = FeesGroupSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        fee_group = self.request.query_params.get('fee_group')
        group_type = self.request.query_params.get('group_type')
        
        if fee_group:
            queryset = queryset.filter(fee_group=fee_group)
        if group_type:
            queryset = queryset.filter(group_type=group_type)
            
        return queryset.order_by('fee_group', 'group_type')

@method_decorator(module_required('fees', 'view'), name='list')
@method_decorator(module_required('fees', 'edit'), name='create')
class FeesTypeViewSet(viewsets.ModelViewSet):
    queryset = FeesType.objects.select_related('fee_group', 'related_stoppage')
    serializer_class = FeesTypeSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        fee_group_id = self.request.query_params.get('fee_group_id')
        class_name = self.request.query_params.get('class_name')
        
        if fee_group_id:
            queryset = queryset.filter(fee_group_id=fee_group_id)
        if class_name:
            queryset = queryset.filter(class_name=class_name)
            
        return queryset.order_by('fee_group__fee_group', 'group_type')
    
    @action(detail=False, methods=['get'])
    def by_class(self, request):
        """Get fee types by class"""
        class_name = request.query_params.get('class_name')
        
        if not class_name:
            return Response({'error': 'Class name is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        fee_types = self.get_queryset().filter(class_name=class_name)
        serializer = self.get_serializer(fee_types, many=True)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Bulk create fee types"""
        try:
            fee_types_data = request.data.get('fee_types', [])
            
            if not fee_types_data:
                return Response({'error': 'No fee types data provided'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            created_count = 0
            errors = []
            
            for fee_data in fee_types_data:
                serializer = self.get_serializer(data=fee_data)
                if serializer.is_valid():
                    serializer.save()
                    created_count += 1
                else:
                    errors.append(serializer.errors)
            
            return Response({
                'message': f'Created {created_count} fee types',
                'created_count': created_count,
                'errors': errors
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)