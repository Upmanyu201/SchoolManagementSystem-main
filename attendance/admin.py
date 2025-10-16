from django.contrib import admin
from .models import Attendance

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'status', 'get_class_name', 'get_section_name')
    list_filter = ('status', 'class_section', 'date')
    search_fields = ('student__first_name', 'student__last_name', 'student__admission_number')
    date_hierarchy = 'date'
    
    def get_class_name(self, obj):
        return obj.class_section.class_name if obj.class_section else obj.student.class_section.class_name if obj.student.class_section else '-'
    get_class_name.short_description = 'Class'
    
    def get_section_name(self, obj):
        return obj.class_section.section_name if obj.class_section else obj.student.class_section.section_name if obj.student.class_section else '-'
    get_section_name.short_description = 'Section'