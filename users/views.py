from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from django.db import models, IntegrityError

User = get_user_model()
from .models import UserModulePermission
from .forms import ModulePermissionForm
from .decorators import superuser_required, module_required

@login_required
@superuser_required
def add_user_view(request):
    """Add new user view"""
    if request.method == 'POST':
        from .forms import AddUserForm
        form = AddUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Excellent! User '{user.username}' has been created successfully.")
            return redirect('users:user_management')
        else:
            messages.error(request, "Please fix the highlighted issues and try again.")
    else:
        from .forms import AddUserForm
        form = AddUserForm()
    
    return render(request, 'users/add_user.html', {'form': form})

@login_required
@superuser_required
def module_access_view(request):
    """2025 Industry Standard: Module access management"""
    import logging
    logger = logging.getLogger(__name__)
    
    if request.method == 'POST':
        logger.info(f"🔐 Module Access POST request from user: {request.user.username}")
        
        selected_user_id = request.POST.get('user')
        if not selected_user_id:
            messages.error(request, "Please choose a user from the dropdown before saving their permissions.")
            return redirect('users:module_access')
        
        # Check for existing permissions and user validity
        try:
            selected_user = User.objects.get(id=selected_user_id)
            existing_permission = UserModulePermission.objects.filter(user=selected_user).first()
            
            if existing_permission:
                logger.info(f"🔄 Updating existing permissions for {selected_user.username}")
            else:
                logger.info(f"✨ Creating new permissions for {selected_user.username}")
            
        except User.DoesNotExist:
            messages.error(request, "We couldn't find that user. Please refresh the page and try again.")
            return redirect('users:module_access')
        
        form = ModulePermissionForm(request.POST)
        logger.info(f"📋 Form created with {len(form.fields)} fields for user: {selected_user.username}")
        
        if form.is_valid():
            logger.info("✅ Form validation successful")
            
            # Count permissions being set
            permission_count = sum(1 for field_name, value in form.cleaned_data.items() 
                                 if field_name != 'user' and value)
            logger.info(f"📊 Setting {permission_count} permissions")
            
            try:
                form.save()
                action = "updated" if existing_permission else "created"
                messages.success(
                    request, 
                    f"Perfect! Module permissions {action} for {selected_user.get_full_name() or selected_user.username}."
                )
                return redirect('users:module_access')
            except Exception as e:
                logger.error(f"❌ Error saving permissions: {e}")
                messages.error(request, "Something went wrong while saving the permissions. Please try again.")
        else:
            logger.error("❌ Form validation failed")
            logger.error(f"🔍 Form errors: {form.errors}")
            logger.error(f"🔍 Non-field errors: {form.non_field_errors()}")
            
            # Provide specific error messages
            for field, errors in form.errors.items():
                for error in errors:
                    if error.strip():  # Only show non-empty errors
                        field_display = field.replace('_', ' ').title()
                        messages.error(request, f"{field_display}: {error}")
                        logger.error(f"🚨 Field error - {field}: {error}")
            
            # If no specific errors, show generic message
            if not any(error.strip() for errors in form.errors.values() for error in errors):
                messages.error(request, "Please fix the form issues highlighted above and try again.")
    else:
        logger.info(f"📄 Module Access GET request from user: {request.user.username}")
        
        # Check if user parameter is provided for pre-selection
        selected_user_id = request.GET.get('user')
        if selected_user_id:
            try:
                selected_user = User.objects.get(id=selected_user_id)
                form = ModulePermissionForm(initial={'user': selected_user})
                logger.info(f"📋 Form created with pre-selected user: {selected_user.username}")
            except User.DoesNotExist:
                form = ModulePermissionForm()
                logger.warning(f"⚠️ User with ID {selected_user_id} not found")
        else:
            form = ModulePermissionForm()
            logger.info(f"📋 Empty form created with {len(form.fields)} fields")
    
    # Log context information
    total_users = User.objects.filter(is_superuser=False, is_active=True).count()
    users_with_permissions = UserModulePermission.objects.count()
    
    logger.info(f"📊 Context: {total_users} total users, {users_with_permissions} with permissions")
    
    context = {
        'form': form,
        'title': 'Module Access Control',
        'total_users': total_users,
        'users_with_permissions': users_with_permissions,
        'selected_user_id': request.GET.get('user'),
    }
    
    logger.info("🎯 Rendering module_access.html template")
    
    return render(request, 'users/module_access.html', context)

@login_required
@superuser_required
@require_http_methods(["GET"])
def get_user_permissions(request):
    """API endpoint to get user permissions via AJAX"""
    user_id = request.GET.get('user_id')
    
    if not user_id:
        return JsonResponse({'error': 'Please select a user to view their permissions.'}, status=400)
    
    try:
        user = User.objects.get(id=user_id)
        permissions = UserModulePermission.get_user_permissions(user)
        
        return JsonResponse({
            'success': True,
            'permissions': permissions,
            'user_name': user.get_full_name() or user.username
        })
    
    except User.DoesNotExist:
        return JsonResponse({'error': 'We couldn\'t find that user. Please refresh and try again.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': 'Something went wrong while loading user permissions. Please try again.'}, status=500)

@login_required
@module_required('users', 'view')
def user_management(request):
    """User management view with module access control"""
    from django.core.paginator import Paginator
    
    # Get all users
    users = User.objects.select_related().order_by('-date_joined')
    
    # Apply search filter
    search = request.GET.get('search')
    if search:
        users = users.filter(
            models.Q(username__icontains=search) |
            models.Q(first_name__icontains=search) |
            models.Q(last_name__icontains=search) |
            models.Q(email__icontains=search)
        )
    
    # Apply role filter
    role = request.GET.get('role')
    if role:
        if role == 'superuser':
            users = users.filter(is_superuser=True)
        else:
            users = users.filter(role=role)
    
    # Pagination
    paginator = Paginator(users, 20)  # 20 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'users': page_obj,  # For backward compatibility
        'total_users': users.count(),
        'title': 'User Management'
    }
    
    return render(request, 'users/user_management.html', context)

@login_required
@superuser_required
async def bulk_permission_update(request):
    """Bulk update permissions for multiple users"""
    
    if request.method == 'POST':
        user_ids = request.POST.getlist('user_ids')
        permission_template = request.POST.get('permission_template')
        
        if not user_ids:
            messages.error(request, "Please choose at least one user to update their permissions.")
            return redirect('users:module_access')
        
        # Define permission templates
        templates = {
            'teacher': {
                'students_view': True, 'subjects_view': True, 'attendance_view': True, 
                'attendance_edit': True
            },
            'accountant': {
                'fees_view': True, 'fees_edit': True, 'payments_view': True, 
                'payments_edit': True, 'fines_view': True, 'reports_view': True
            },
            'admin_staff': {
                'students_view': True, 'students_edit': True, 'teachers_view': True,
                'subjects_view': True, 'transport_view': True, 'transport_edit': True,
                'reports_view': True
            }
        }
        
        if permission_template not in templates:
            messages.error(request, "Please select a valid permission template from the dropdown.")
            return redirect('users:module_access')
        
        permissions_data = templates[permission_template]
        updated_count = 0
        
        for user_id in user_ids:
            try:
                user = await User.objects.aget(id=user_id)
                permission, created = await UserModulePermission.objects.aget_or_create(
                    user=user,
                    defaults=permissions_data
                )
                
                if not created:
                    for field, value in permissions_data.items():
                        setattr(permission, field, value)
                    await permission.asave()
                
                updated_count += 1
                
            except User.DoesNotExist:
                continue
        
        messages.success(
            request, 
            f"Perfect! We've updated permissions for {updated_count} users using the {permission_template.replace('_', ' ').title()} template."
        )
    
    return redirect('users:module_access')

@login_required
@superuser_required
async def reset_user_permissions(request, user_id):
    """Reset all permissions for a specific user"""
    
    try:
        user = await User.objects.aget(id=user_id)
        
        try:
            permission = await UserModulePermission.objects.aget(user=user)
            await permission.adelete()
            messages.success(
                request, 
                f"Perfect! All permissions have been reset for {user.get_full_name() or user.username}."
            )
        except UserModulePermission.DoesNotExist:
            messages.info(request, f"{user.get_full_name() or user.username} doesn't have any permissions set up yet.")
    
    except User.DoesNotExist:
        messages.error(request, "We couldn't find that user. Please check your selection.")
    
    return redirect('users:module_access')

@login_required
async def check_module_access(request):
    """API endpoint to check if user has module access"""
    module_name = request.GET.get('module')
    permission_type = request.GET.get('type', 'view')
    
    if not module_name:
        return JsonResponse({'error': 'Please specify which module you want to check access for.'}, status=400)
    
    permissions = UserModulePermission.get_user_permissions(request.user)
    has_access = permissions.get(module_name, {}).get(permission_type, False)
    
    return JsonResponse({
        'has_access': has_access,
        'module': module_name,
        'permission_type': permission_type
    })

@login_required
@module_required('users', 'edit')
def edit_user(request, user_id):
    """Edit user profile and permissions"""
    target_user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        if form_type == 'profile':
            # Update basic profile info
            target_user.first_name = request.POST.get('first_name', '')
            target_user.last_name = request.POST.get('last_name', '')
            target_user.email = request.POST.get('email', '')
            target_user.role = request.POST.get('role', target_user.role)
            target_user.is_active = request.POST.get('is_active') == 'on'
            
            # Check mobile number uniqueness
            if 'mobile' in request.POST:
                new_mobile = request.POST.get('mobile', '').strip()
                if new_mobile and User.objects.filter(mobile=new_mobile).exclude(id=target_user.id).exists():
                    messages.error(request, f"Sorry, the mobile number {new_mobile} is already registered with another user. Please use a different number.")
                    return redirect('users:edit_user', user_id=user_id)
                target_user.mobile = new_mobile
            
            try:
                target_user.save()
                messages.success(request, f"Great! Profile has been updated successfully for {target_user.get_full_name() or target_user.username}.")
            except Exception as e:
                messages.error(request, "Sorry, we couldn't save the changes. Please check all fields and try again.")
                return redirect('users:edit_user', user_id=user_id)
        
        elif form_type == 'permissions':
            # Update module permissions
            permission, created = UserModulePermission.objects.get_or_create(user=target_user)
            
            modules = ['students', 'teachers', 'subjects', 'fees', 'payments', 
                      'fines', 'attendance', 'transport', 'reports', 'messaging', 
                      'promotion', 'users', 'settings', 'backup', 'school_profile']
            
            for module in modules:
                setattr(permission, f"{module}_view", request.POST.get(f"{module}_view") == 'on')
                setattr(permission, f"{module}_edit", request.POST.get(f"{module}_edit") == 'on')
            
            permission.save()
            messages.success(request, f"Perfect! Permissions have been updated successfully for {target_user.get_full_name() or target_user.username}.")

        elif form_type == 'password':

            if not request.user.is_superuser:
                messages.error(request, "Access Denied: You must be a Superuser to reset passwords.")
                return redirect('users:edit_user', user_id=user_id)
            new_password = request.POST.get('new_password', '').strip()
            if new_password:
                target_user.set_password(new_password)                
                target_user.save()                              
                messages.success(request, f"🔒 Password for '{target_user.username}' has been successfully reset.")
            else:
                messages.error(request, "Password reset failed: Please provide a value for the new password.")            
                return redirect('users:edit_user', user_id=user_id)

 

   
        return redirect('users:edit_user', user_id=user_id)

    
    # Get user permissions
    try:
        user_permissions = UserModulePermission.objects.get(user=target_user)
    except UserModulePermission.DoesNotExist:
        user_permissions = None
    
    context = {
        'target_user': target_user,
        'user_permissions': user_permissions,
        'title': f'Edit User - {target_user.get_full_name() or target_user.username}'
    }
    
    return render(request, 'users/edit_user.html', context)

@login_required
@superuser_required
def user_activity_log(request):
    """User activity log view - simple implementation"""
    from django.contrib.admin.models import LogEntry
    from django.core.paginator import Paginator
    
    # Get user filter
    user_id = request.GET.get('user_id')
    selected_user = None
    
    # Get Django admin log entries as activity
    activities = LogEntry.objects.select_related('user', 'content_type').order_by('-action_time')
    
    if user_id:
        try:
            selected_user = User.objects.get(id=user_id)
            activities = activities.filter(user=selected_user)
        except User.DoesNotExist:
            messages.error(request, "User not found.")
    
    # Pagination
    paginator = Paginator(activities, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all users for filter dropdown
    all_users = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
    
    context = {
        'page_obj': page_obj,
        'activities': page_obj,
        'selected_user': selected_user,
        'all_users': all_users,
        'title': 'User Activity Log'
    }
    
    return render(request, 'users/activity_log.html', context)

def logout_view(request):
    """Custom logout view that handles both GET and POST"""
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, "You've been logged out successfully. Thanks for using our system!")
    return redirect('users:login')

@login_required
@superuser_required
@require_http_methods(["POST"])
def clear_user_cache(request, user_id):
    """Clear user cache via AJAX"""
    try:
        user = User.objects.get(id=user_id)
        
        # Clear Django cache for this user
        from django.core.cache import cache
        cache_keys = [
            f'user_permissions_{user_id}',
            f'user_modules_{user_id}',
            f'user_profile_{user_id}'
        ]
        
        for key in cache_keys:
            cache.delete(key)
        
        return JsonResponse({
            'success': True,
            'message': f'Cache cleared successfully for {user.get_full_name() or user.username}'
        })
    
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'User not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Error clearing cache'
        }, status=500)

@login_required
@superuser_required
@require_http_methods(["POST"])
def toggle_user_status(request, user_id):
    """Toggle user active status via AJAX"""
    try:
        user = User.objects.get(id=user_id)
        
        if user.id == request.user.id:
            return JsonResponse({
                'success': False,
                'message': 'You cannot deactivate your own account'
            }, status=400)
        
        user.is_active = not user.is_active
        user.save()
        
        status = 'activated' if user.is_active else 'deactivated'
        return JsonResponse({
            'success': True,
            'message': f'User {status} successfully',
            'is_active': user.is_active
        })
    
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'User not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Error updating user status'
        }, status=500)

# Context processor for template access
def module_permissions_context(request):
    """Add user module permissions to template context"""
    if request.user.is_authenticated:
        permissions = UserModulePermission.get_user_permissions(request.user)
        return {'user_module_permissions': permissions}
    return {'user_module_permissions': {}}