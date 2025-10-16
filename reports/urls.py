# reports/urls.py
from django.urls import path
from . import views
from . import api_views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_dashboard, name='reports'),
    path('fees-report/', views.fees_report, name='fees_report'),
    path('send-reminder/', views.send_fee_reminder, name='send_fee_reminder'),
    path('api/dashboard-data/', views.dashboard_api_data, name='dashboard_api_data'),
    
    # REST API endpoints
    path('api/fees-report/', api_views.fees_report_api, name='api_fees_report'),
    path('api/attendance-report/', api_views.attendance_report_api, name='api_attendance_report'),
    path('api/dashboard-summary/', api_views.dashboard_summary_api, name='api_dashboard_summary'),
]
