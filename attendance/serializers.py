# attendance/serializers.py
from rest_framework import serializers
from .models import Attendance
from students.models import Student

class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    admission_number = serializers.CharField(source='student.admission_number', read_only=True)
    class_name = serializers.CharField(source='student.class_section.class_name', read_only=True)
    
    class Meta:
        model = Attendance
        fields = ['id', 'student', 'student_name', 'admission_number', 'class_name', 'date', 'status', 'created_at']
        read_only_fields = ['created_at']

class BulkAttendanceSerializer(serializers.Serializer):
    class_id = serializers.IntegerField()
    date = serializers.DateField()
    attendance = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )