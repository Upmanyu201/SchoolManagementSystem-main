from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from .models import SchoolProfile
from .forms import SchoolProfileForm
from users.decorators import module_required

@module_required('school_profile', 'view')
def school_profile_view(request):
    try:
        profile = SchoolProfile.objects.get()
    except SchoolProfile.DoesNotExist:
        profile = None
        messages.warning(request, "School profile not created yet")

    return render(request, 'school_profile/profile_view.html', {'profile': profile})

@module_required('school_profile', 'edit')
def school_profile_edit(request):
    try:
        profile = SchoolProfile.objects.get()
    except SchoolProfile.DoesNotExist:
        profile = None

    if request.method == 'POST':
        form = SchoolProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "School profile updated successfully")
            return redirect('school_profile_view')
    else:
        form = SchoolProfileForm(instance=profile)

    return render(request, 'school_profile/edit.html', {'form': form})