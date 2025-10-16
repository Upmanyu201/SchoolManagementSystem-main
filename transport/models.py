from django.db import models
from django.utils.html import escape
from students.models import Student  # Import Student Model

class Route(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Route Name")

    def __str__(self):
        return escape(self.name)

class Stoppage(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, verbose_name="Route")
    name = models.CharField(max_length=100, unique=True, verbose_name="Stoppage Name")

    class Meta:
        unique_together = ('route', 'name')  # Ensure unique stoppages per route

    def __str__(self):
        return escape(f"{self.route} - {self.name}")

class TransportAssignment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="Student")
    route = models.ForeignKey(Route, on_delete=models.CASCADE, verbose_name="Route")
    stoppage = models.ForeignKey(Stoppage, on_delete=models.CASCADE, verbose_name="Stoppage")
    assigned_date = models.DateField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student'], name='unique_student_per_route'),
            #models.UniqueConstraint(fields=['student', 'stoppage'], name='unique_student_per_stoppage'),
        ]
    
    @property
    def get_full_display_name(self):
        return escape(f"{self.student.first_name} {self.student.last_name} ({self.route.name})")

    def __str__(self):
        return escape(f"{self.student.first_name} - {self.route} - {self.stoppage}")
