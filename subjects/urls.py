from django.urls import path
from . import views

urlpatterns = [
    path('', views.subjects_management, name='subjects_management'),
    
    # Class-Section URLs
    path('add-class-section/', views.add_class_section, name='add_class_section'),
    path('edit-class-section/<int:pk>/', views.edit_class_section, name='edit_class_section'),
    path('delete-class-section/<int:pk>/', views.delete_class_section, name='delete_class_section'),
    
    # Subject URLs
    path('add-subject/', views.add_subject, name='add_subject'),
    path('edit-subject/<int:pk>/', views.edit_subject, name='edit_subject'),
    path('delete-subject/<int:pk>/', views.delete_subject, name='delete_subject'),
    
    # Subject Assignment URLs
    path('add-subject-assignment/', views.add_subject_assignment, name='add_subject_assignment'),
    path('edit-subject-assignment/<int:pk>/', views.edit_subject_assignment, name='edit_subject_assignment'),
    path('delete-subject-assignment/<int:pk>/', views.delete_subject_assignment, name='delete_subject_assignment'),
    # Export URLs removed - export system discontinued
    path('import-csv/', views.import_csv, name='import_csv'),
]