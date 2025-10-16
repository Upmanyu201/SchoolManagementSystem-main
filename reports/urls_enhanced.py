# Enhanced URLs for Payment History APIs
from django.urls import path
from . import views_enhanced

app_name = 'reports'

urlpatterns = [
    # Enhanced fees report with advanced filtering
    path('fees-enhanced/', views_enhanced.enhanced_fees_report, name='fees_report_enhanced'),
    
    # API endpoints for AJAX/HTMX requests
    path('api/payment-summary/', views_enhanced.payment_summary_api, name='payment_summary_api'),
    path('api/payment-trend/', views_enhanced.payment_trend_api, name='payment_trend_api'),
    path('api/ml-insights/', views_enhanced.ml_insights_api, name='ml_insights_api'),
]