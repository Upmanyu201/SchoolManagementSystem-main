# core/fee_management/apps.py
from django.apps import AppConfig

class FeeManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core.fee_management'
    label = 'fee_management'