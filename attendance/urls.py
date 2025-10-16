from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .api_views import AttendanceViewSet

app_name = 'attendance'

# API Router
router = DefaultRouter()
router.register(r'attendance', AttendanceViewSet)

urlpatterns = [
    path('', views.attendance_manage, name='attendance'),
    path('manage/', views.attendance_manage, name='attendance_manage'),
    path('get_students/<int:class_section_id>/', views.get_students, name='get_students'),
    path('get_previous/', views.get_previous_attendance, name='get_previous_attendance'),
    path('mark/', views.mark_attendance, name='mark_attendance'),
    path('report/', views.attendance_report, name='attendance_report'),
    path('professional-report/', views.professional_attendance_report, name='professional_attendance_report'),
    
    # API endpoints
    path('api/', include(router.urls)),
]