from django.urls import path
from .views import school_profile_view, school_profile_edit

urlpatterns = [
    path('', school_profile_view, name='school_profile_view'),
    path('edit/', school_profile_edit, name='school_profile_edit'),
]
