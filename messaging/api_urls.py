"""
WhatsApp API URLs
"""

from django.urls import path
from . import api_views

urlpatterns = [
    path('send-whatsapp/', api_views.send_whatsapp_api, name='send_whatsapp_api'),
    path('bulk-whatsapp/', api_views.bulk_whatsapp_api, name='bulk_whatsapp_api'),
    path('status/', api_views.whatsapp_status, name='whatsapp_status'),
]