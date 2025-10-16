# fees/serializers.py
from rest_framework import serializers
from .models import FeesGroup, FeesType

class FeesGroupSerializer(serializers.ModelSerializer):
    class_section_name = serializers.CharField(source='related_class_section.class_name', read_only=True)
    stoppage_name = serializers.CharField(source='related_stoppage.stoppage_name', read_only=True)
    
    class Meta:
        model = FeesGroup
        fields = ['id', 'fee_group', 'group_type', 'fee_type', 'related_class_section', 
                 'class_section_name', 'related_stoppage', 'stoppage_name', 'created_at']
        read_only_fields = ['created_at']

class FeesTypeSerializer(serializers.ModelSerializer):
    fee_group_name = serializers.CharField(source='fee_group.fee_group', read_only=True)
    stoppage_name = serializers.CharField(source='related_stoppage.stoppage_name', read_only=True)
    
    class Meta:
        model = FeesType
        fields = ['id', 'fee_group', 'fee_group_name', 'group_type', 'fee_type', 
                 'amount_type', 'amount', 'class_name', 'related_stoppage', 
                 'stoppage_name', 'created_at']
        read_only_fields = ['created_at']