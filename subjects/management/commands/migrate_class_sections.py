from django.core.management.base import BaseCommand
from subjects.models import Class, Section, ClassSection
from students.models import Student

class Command(BaseCommand):
    help = 'Migrate existing classes and sections to ClassSection model'
    
    def handle(self, *args, **options):
        # Create ClassSection from existing Class and Section combinations
        classes = Class.objects.all()
        sections = Section.objects.all()
        
        for cls in classes:
            for section in sections:
                # Check if students exist for this combination
                if Student.objects.filter(student_class=cls, student_section=section).exists():
                    class_section, created = ClassSection.objects.get_or_create(
                        class_name=cls.name,
                        section_name=section.name,
                        defaults={'room_number': f"R-{cls.name}-{section.name}"}
                    )
                    if created:
                        self.stdout.write(f"Created: {class_section}")
        
        self.stdout.write(self.style.SUCCESS('Migration completed successfully'))