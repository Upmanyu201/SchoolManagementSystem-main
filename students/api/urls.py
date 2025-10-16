from django.urls import path
from . import dashboard

urlpatterns = [
    path('dashboard/<int:student_id>/', dashboard.student_dashboard_api, name='student_dashboard_api'),
]