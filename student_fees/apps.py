from django.apps import AppConfig


class StudentFeesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'student_fees'
    
    def ready(self):
        import student_fees.signals
