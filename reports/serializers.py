# reports/serializers.py
from rest_framework import serializers

class ReportDataSerializer(serializers.Serializer):
    student_name = serializers.CharField()
    admission_number = serializers.CharField()
    class_name = serializers.CharField()
    
class FeesReportSerializer(ReportDataSerializer):
    fee_type = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount = serializers.DecimalField(max_digits=10, decimal_places=2)
    deposit_date = serializers.DateField()
    receipt_no = serializers.CharField()

class AttendanceReportSerializer(ReportDataSerializer):
    total_days = serializers.IntegerField()
    present_days = serializers.IntegerField()
    absent_days = serializers.IntegerField()
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)

class DashboardSummarySerializer(serializers.Serializer):
    students = serializers.DictField()
    fees = serializers.DictField()
    fines = serializers.DictField()