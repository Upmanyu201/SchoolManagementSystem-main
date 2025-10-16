# Core URLs - Clean
from django.urls import path, include
from . import api_views

app_name = 'core'

urlpatterns = [
    # Export API
    path('api/export/initiate/', api_views.export_initiate, name='export_initiate'),
    path('api/export/status/<str:request_id>/', api_views.export_status, name='export_status'),
    path('api/export/download/<str:request_id>/', api_views.export_download, name='export_download'),
]