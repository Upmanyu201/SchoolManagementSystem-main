from django.apps import AppConfig
import os

class FeesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'fees'
    label = 'fees'

    def ready(self):
        # Signals removed - handled by centralized service
        template_dir = os.path.join(self.path, 'templates')
        self.template_dirs = [template_dir]