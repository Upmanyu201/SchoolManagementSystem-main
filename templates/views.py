from django.shortcuts import render
from school_profile.models import SchoolProfile  # Import the correct model

def get_academic_session():
    """Fetch the academic session from the database"""
    school_profile = SchoolProfile.objects.first()  # Get the first profile
    if school_profile:
        return {
            "start_year": school_profile.start_date.year,
            "end_year": school_profile.end_date.year
        }
    return {"start_year": "N/A", "end_year": "N/A"}

def dashboard_view(request):
    """Dashboard view with academic session data"""
    academic_session = get_academic_session()
    return render(request, "dashboard.html", {"academic_session": academic_session})


def school_profile_view(request):
    """School Profile Page"""
    school_profile = SchoolProfile.objects.first()  # Get the school profile
    academic_session = get_academic_session()  # Fetch academic session

    context = {
        "profile": school_profile,
        "academic_session": academic_session,  # ✅ Now passing academic session
    }
    return render(request, "profile_view.html", context)