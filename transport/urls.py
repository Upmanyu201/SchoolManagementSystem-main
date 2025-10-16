from django.urls import path
from . import views, api_views

from django.views.decorators.http import require_POST

urlpatterns = [
    # Main views
    path('', views.transport_management, name='transport_management'),
    path('delete-route/<int:route_id>/', require_POST(views.delete_route), name='delete_route'),
    path('delete-stoppage/<int:stoppage_id>/', require_POST(views.delete_stoppage), name='delete_stoppage'),
    path('delete-assignment/<int:assignment_id>/', require_POST(views.delete_assignment), name='delete_assignment'),
    path('assignments/', views.transport_assignments_list, name='transport_assignments_list'),
    path('routes/', views.all_routes, name='all_routes'),
    path('stoppages/', views.all_stoppages, name='all_stoppages'),
    
    # API endpoints
    path('api/search-students/', api_views.search_students_api, name='search_students_api'),
    path('api/route/<int:route_id>/stoppages/', api_views.get_route_stoppages_api, name='route_stoppages_api'),
    path('api/validate-assignment/', api_views.validate_assignment_api, name='validate_assignment_api'),
    path('api/stats/', api_views.TransportStatsAPI.as_view(), name='transport_stats_api'),
    path('api/suggest-routes/', api_views.suggest_routes_by_address, name='suggest_routes_api'),
    

]
