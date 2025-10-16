from django.core.management.base import BaseCommand
from students.models import Student
from subjects.models import ClassSection
from datetime import date

class Command(BaseCommand):
    help = 'Update all student classes based on their age'

    def handle(self, *args, **options):
        # Age to class mapping
        age_to_class = {
            3: 'Nursary',
            4: 'LKG', 
            5: 'UKG',
            6: 'Class 1',
            7: 'Class 2',
            8: 'Class 3',
            9: 'Class 4',
            10: 'Class 5',
            11: 'Class 6',
            12: 'Class 7',
            13: 'Class 8',
            14: 'Class 9',
            15: 'Class 10',
        }

        updated_count = 0
        
        for student in Student.objects.all():
            if student.date_of_birth:
                # Calculate age
                today = date.today()
                age = today.year - student.date_of_birth.year - ((today.month, today.day) < (student.date_of_birth.month, student.date_of_birth.day))
                
                # Get appropriate class
                class_name = age_to_class.get(age)
                
                if class_name:
                    try:
                        class_section = ClassSection.objects.filter(class_name=class_name).first()
                        if class_section and student.class_section != class_section:
                            student.class_section = class_section
                            student.save()
                            updated_count += 1
                            self.stdout.write(f'Updated {student.name} (age {age}) to {class_name}')
                        elif not class_section:
                            self.stdout.write(self.style.WARNING(f'Class "{class_name}" not found'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error updating student {student.name}: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} students'))