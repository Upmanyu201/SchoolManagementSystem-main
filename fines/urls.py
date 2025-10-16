from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api  # API enabled

app_name = 'fines'

# Set up the API router
router = DefaultRouter()
router.register(r'fines', api.FineViewSet)
router.register(r'fine-types', api.FineTypeViewSet)
router.register(r'fine-students', api.FineStudentViewSet)

urlpatterns = [
    # Traditional views
    path('add/', views.add_fine, name='add_fine'),
    path('history/', views.fine_history, name='fine_history'),
    path('deactivate/<int:fine_id>/', views.deactivate_fine, name='deactivate_fine'),
    path('waive-fines/', views.waive_fines, name='waive_fines'),
    path('delete/<int:fine_id>/', views.delete_fine, name='delete_fine'),
    path('upload/', views.upload_fines, name='upload_fines'),
    path('', views.base_fine, name='base_fine'),
    # Export endpoint removed
    path('edit/<int:fine_id>/', views.edit_fine, name='edit_fine'),
    
    # Fine Type Management
    path('types/', views.fine_types, name='fine_types'),
    path('types/add/', views.add_fine_type, name='add_fine_type'),
    path('types/edit/<int:fine_type_id>/', views.edit_fine_type, name='edit_fine_type'),
    path('types/toggle-status/<int:fine_type_id>/', views.toggle_fine_type_status, name='toggle_fine_type_status'),
    path('types/delete/<int:fine_type_id>/', views.delete_fine_type, name='delete_fine_type'),
    
    # AJAX endpoints
    path('ajax/load-students/', views.load_students_for_class, name='ajax_load_students'),
    path('ajax/load-fees-types/', views.load_fees_types, name='ajax_load_fees_types'),
    path('ajax/load-classes-for-fees-type/', views.load_classes_for_fees_type, name='ajax_load_classes_for_fees_type'),
    path('ajax/load-students-for-fees-type/', views.load_students_for_fees_type, name='ajax_load_students_for_fees_type'),
    path('ajax/search-students/', views.search_students, name='ajax_search_students'),
    path('ajax/download-sample-csv/', views.download_sample_csv, name='ajax_download_sample_csv'),
    path('download-sample-csv/', views.download_sample_csv, name='download_sample_csv'),
    path('ajax/get-fine-type-usage/<int:fine_type_id>/', views.get_fine_type_usage, name='ajax_get_fine_type_usage'),
    path('ajax/get-fee-types-for-group/', views.get_fee_types_for_group, name='ajax_get_fee_types_for_group'),
    path('ajax/get-classes-for-fee-types/', views.get_classes_for_fee_types, name='ajax_get_classes_for_fee_types'),
    
    # API endpoints
    path('api/', include(router.urls)),
    
    # Export endpoints
    path('export/csv/', views.export_fines_csv, name='export_fines_csv'),
    
    # Verification and Analysis endpoints
    path('verify/<int:fine_id>/', views.verify_fine_application, name='verify_fine_application'),
    path('fix/<int:fine_id>/', views.fix_fine_application, name='fix_fine_application'),
    path('analyze-fee-type/<int:fees_type_id>/', views.analyze_fee_type, name='analyze_fee_type'),
]