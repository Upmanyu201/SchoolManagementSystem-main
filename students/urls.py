from django.urls import path, include
from . import views
from . import student_dashboard_views
from . import api_views
from . import fee_calculation_api
from . import dashboard_api
from . import transport_api
from .debug_students import debug_students_count
from .simple_test import simple_student_list
from .coordination_test import coordination_test, coordination_api


app_name = 'students'

urlpatterns = [
    # API URLs
    path('api/', include('students.api.urls')),
    # Main student views
    path('', views.student_list, name='student_list'),
    path('add/', views.add_student, name='add_student'),
    path('edit/<int:id>/', views.edit_student, name='edit_student'),
    path('delete/<int:id>/', views.delete_student, name='delete_student'),
    path('change-status/<int:id>/', views.change_student_status, name='change_student_status'),
    path('api/status-counts/', views.get_status_counts, name='get_status_counts'),

    # Student-Centric Dashboard URLs
    path('dashboard/<str:admission_number>/', student_dashboard_views.student_unified_dashboard, name='student_dashboard'),
    
    # Optimized API Endpoints
    path('api/search/', api_views.search_students_api, name='search_students_api'),
    path('api/stats/', api_views.students_stats_api, name='students_stats_api'),
    path('api/bulk-update-dues/', api_views.bulk_update_dues_api, name='bulk_update_dues_api'),
    path('api/validate-admission/', api_views.validate_admission_number_api, name='validate_admission_api'),
    path('api/quick-info/<int:student_id>/', api_views.student_quick_info_api, name='student_quick_info_api'),
    
    # Dashboard API Endpoints
    path('api/dashboard/<str:admission_number>/', api_views.student_dashboard_api, name='student_dashboard_api'),
    path('api/live-dashboard/<str:admission_number>/', dashboard_api.student_live_dashboard_api, name='student_live_dashboard_api'),
    path('api/timeline/<str:admission_number>/', student_dashboard_views.student_timeline_api, name='student_timeline_api'),
    path('api/payment/<str:admission_number>/', student_dashboard_views.student_payment_api, name='student_payment_api'),

    
    # Legacy API Endpoints (for backward compatibility)
    path('api/students/<str:admission_number>/payments/', api_views.student_payments_api, name='student_payments_api'),
    path('debug/<str:admission_number>/', views.debug_transport, name='debug_transport'),
    path('debug-count/', debug_students_count, name='debug_students_count'),
    path('debug-pagination/', views.debug_pagination, name='debug_pagination'),
    path('simple-test/', simple_student_list, name='simple_test'),
    path('coordination-test/', coordination_test, name='coordination_test'),
    path('coordination-api/', coordination_api, name='coordination_api'),
    path('api/search-legacy/', student_dashboard_views.student_search_api, name='student_search_api_legacy'),
    
    # Fee Calculation API Endpoints
    path('api/fees/<str:admission_number>/summary/', fee_calculation_api.get_student_fee_summary, name='fee_summary_api'),
    path('api/fees/<str:admission_number>/breakdown/', fee_calculation_api.get_payment_breakdown, name='payment_breakdown_api'),
    path('api/fees/<str:admission_number>/preview/', fee_calculation_api.calculate_payment_preview, name='payment_preview_api'),
    path('api/fees/<str:admission_number>/process/', fee_calculation_api.process_fee_payment, name='process_payment_api'),
    path('api/fees/<str:admission_number>/history/', fee_calculation_api.get_payment_history, name='payment_history_api'),
    path('api/fees/<str:admission_number>/refresh/', fee_calculation_api.refresh_student_calculations, name='refresh_calculations_api'),
]
