"""Make academic session available globally in all templates"""

from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.apps import apps


def academic_session_context(request):
    """Make academic session available globally in all templates"""
    # Only access database if Django is fully initialized
    if not apps.ready:
        current_year = timezone.now().year
        return {
            "academic_session": {
                "current": f"{current_year}-{current_year + 1}",
                "next": f"{current_year + 1}-{current_year + 2}",
                "start_year": current_year,
                "end_year": current_year + 1,
            }
        }
    
    try:
        from school_profile.models import SchoolProfile
        school_profile = SchoolProfile.objects.first()
        if not school_profile:
            raise ObjectDoesNotExist

        return {
            "academic_session": {
                "current": f"{school_profile.start_date.year}-{school_profile.end_date.year}",
                "next": f"{school_profile.start_date.year + 1}-{school_profile.end_date.year + 1}",
                "start_year": school_profile.start_date.year,
                "end_year": school_profile.end_date.year,
            }
        }
    except (ObjectDoesNotExist, AttributeError, Exception) as e:
        current_year = timezone.now().year
        return {
            "academic_session": {
                "current": f"{current_year}-{current_year + 1}",
                "next": f"{current_year + 1}-{current_year + 2}",
                "start_year": current_year,
                "end_year": current_year + 1,
            }
        }
    
# This context processor can be added to the TEMPLATES setting in settings.py
# under the 'OPTIONS' key, like this:   
