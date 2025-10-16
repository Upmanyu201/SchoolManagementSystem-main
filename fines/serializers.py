# fines/serializers.py
from rest_framework import serializers
from .models import Fine, FineType, FineStudent

class FineTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FineType
        fields = ['id', 'name', 'amount', 'description', 'created_at']
        read_only_fields = ['created_at']

class FineSerializer(serializers.ModelSerializer):
    fine_type_name = serializers.CharField(source='fine_type.name', read_only=True)
    class_name = serializers.CharField(source='class_section.class_name', read_only=True)
    
    class Meta:
        model = Fine
        fields = ['id', 'fine_type', 'fine_type_name', 'class_section', 'class_name', 
                 'amount', 'description', 'fine_date', 'due_date', 'created_at']
        read_only_fields = ['created_at']

class FineStudentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    admission_number = serializers.CharField(source='student.admission_number', read_only=True)
    fine_type_name = serializers.CharField(source='fine.fine_type.name', read_only=True)
    fine_amount = serializers.DecimalField(source='fine.amount', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = FineStudent
        fields = ['id', 'fine', 'student', 'student_name', 'admission_number', 
                 'fine_type_name', 'fine_amount', 'is_paid', 'is_waived', 
                 'payment_date', 'waived_date', 'created_at']
        read_only_fields = ['created_at']