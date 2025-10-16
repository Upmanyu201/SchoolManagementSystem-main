# students/serializers.py
from rest_framework import serializers
from .models import Student

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = '__all__'

class StudentDashboardSerializer(serializers.Serializer):
    """Serializer for complete student dashboard data"""
    student = StudentSerializer()
    fees = serializers.ListField()
    attendance = serializers.ListField()
    transport = serializers.DictField(allow_null=True)
    fines = serializers.ListField()
    financial_summary = serializers.DictField()
    academic_summary = serializers.DictField()