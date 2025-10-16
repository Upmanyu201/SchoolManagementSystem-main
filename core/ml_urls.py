from django.urls import path
from .ml_api_views import test_ml_integration, ml_status, ml_dashboard_data

urlpatterns = [
    path('test/', test_ml_integration, name='ml_test'),
    path('status/', ml_status, name='ml_status'),
    path('dashboard/', ml_dashboard_data, name='ml_dashboard_data'),
]