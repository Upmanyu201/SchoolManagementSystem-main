# fees/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .api_views import FeesGroupViewSet, FeesTypeViewSet

app_name = 'fees'

# API Router
router = DefaultRouter()
router.register(r'groups', FeesGroupViewSet)
router.register(r'types', FeesTypeViewSet)

urlpatterns = [
    path('ajax/load-group-types/', views.load_group_types, name='ajax_load_group_types'),
    path('fees_setup/', views.fees_setup, name='fees_setup'),
    path('add-fees-group/', views.add_fees_group, name='add_fees_group'),
    path('edit-fees-group/<int:pk>/', views.edit_fees_group, name='edit_fees_group'),
    path('delete-fees-group/<int:pk>/', views.delete_fees_group, name='delete_fees_group'),
    path('fees-type/add/', views.add_fees_type, name='add_fees_type'),
    path('add-fees-type/', views.add_fees_type, name='add_fees_type'),

    path('fees-type/edit/<int:pk>/', views.edit_fees_type, name='edit_fees_type'),
    path('fees-type/delete/<int:pk>/', views.delete_fees_type, name='delete_fees_type'),
    path('fees-type/bulk-delete/', views.bulk_delete_fees_type, name='bulk_delete_fees_type'),
    path('fees_carry_forward/', views.fees_carry_forward, name='fees_carry_forward'),
    
    # Dynamic fee management API
    path('api/fee-group-context/', views.get_fee_group_context, name='get_fee_group_context'),
    
    # REST API endpoints
    path('api/', include(router.urls)),
]
