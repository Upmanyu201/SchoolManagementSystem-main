from django.urls import path, include
from . import views
from .webhook import whatsapp_webhook
from .enhanced_views import SendMessageView, MessageHistoryView, get_students_by_class, messaging_dashboard as enhanced_dashboard

app_name = 'messaging'

urlpatterns = [
    path('', views.messaging_dashboard, name='dashboard'),
    path('enhanced/', enhanced_dashboard, name='enhanced_dashboard'),
    path('send/', SendMessageView.as_view(), name='send_message'),
    path('enhanced-history/', MessageHistoryView.as_view(), name='enhanced_history'),
    path('ajax/students-by-class/', get_students_by_class, name='students_by_class'),
    path('config/', views.messaging_config, name='config'),
    path('send-individual/', views.send_individual_message, name='send_individual'),
    path('send-bulk/', views.send_bulk_message, name='send_bulk'),
    path('get-class-students/', views.get_class_students, name='get_class_students'),
    path('history/', views.message_history, name='history'),
    path('details/<int:message_id>/', views.message_details, name='details'),
    path('webhook/', whatsapp_webhook, name='webhook'),
    path('test-sms/', views.test_sms, name='test_sms'),
    path('test-page/', views.test_page, name='test_page'),
    # API endpoints
    path('api/', include('messaging.api_urls')),
]