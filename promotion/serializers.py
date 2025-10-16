# promotion/serializers.py
from rest_framework import serializers
from .models import PromotionRule, StudentPromotion

class PromotionRuleSerializer(serializers.ModelSerializer):
    from_class_name = serializers.CharField(source='from_class_section.class_name', read_only=True)
    to_class_name = serializers.CharField(source='to_class_section.class_name', read_only=True)
    
    class Meta:
        model = PromotionRule
        fields = ['id', 'from_class_section', 'from_class_name', 'to_class_section', 
                 'to_class_name', 'minimum_percentage', 'academic_year', 'created_at']
        read_only_fields = ['created_at']

class StudentPromotionSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    admission_number = serializers.CharField(source='student.admission_number', read_only=True)
    from_class_name = serializers.CharField(source='from_class_section.class_name', read_only=True)
    to_class_name = serializers.CharField(source='to_class_section.class_name', read_only=True)
    
    class Meta:
        model = StudentPromotion
        fields = ['id', 'student', 'student_name', 'admission_number', 
                 'from_class_section', 'from_class_name', 'to_class_section', 
                 'to_class_name', 'academic_year', 'promotion_date', 'remarks', 'created_at']
        read_only_fields = ['created_at']

class BulkPromotionSerializer(serializers.Serializer):
    from_class_id = serializers.IntegerField()
    to_class_id = serializers.IntegerField()
    student_ids = serializers.ListField(child=serializers.IntegerField())
    academic_year = serializers.CharField(max_length=10)
    promotion_date = serializers.DateField(required=False)
    remarks = serializers.CharField(required=False, allow_blank=True)