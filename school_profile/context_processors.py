from .models import SchoolProfile

def school_info(request):
    try:
        return {'school': SchoolProfile.objects.first()}
    except SchoolProfile.DoesNotExist:
        return {'school': None}