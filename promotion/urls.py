from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .api_views import PromotionRuleViewSet, StudentPromotionViewSet

app_name = 'promotion'

# API Router
router = DefaultRouter()
router.register(r'rules', PromotionRuleViewSet)
router.register(r'promotions', StudentPromotionViewSet)

urlpatterns = [
    path('', views.student_promotion, name='student_promotion'),
    path('promotion-class/', views.student_promotion, name='promotion_class'),
    path('api/get-students/', views.get_students_by_class, name='get_students_by_class'),
    path('api/promote/', views.promote_students, name='promote_students'),
    
    # REST API endpoints
    path('api/', include(router.urls)),
]