from django.urls import path
from . import views

app_name = 'demo'

urlpatterns = [
    path('status/', views.demo_status, name='status'),
    path('activate/', views.activate_license, name='activate'),
    path('expired/', views.demo_expired, name='expired'),
]