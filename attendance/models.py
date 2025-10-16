from django.db import models
from core.models import BaseModel

class Attendance(BaseModel):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=[('Present', 'Present'), ('Absent', 'Absent')], default='Present')
    class_section = models.ForeignKey('subjects.ClassSection', on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        unique_together = ('student', 'date')
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendance Records'

    def __str__(self):
        return f"{self.student} - {self.date} - {self.status}"
