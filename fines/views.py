from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.utils.html import escape
from users.decorators import module_required
from decimal import Decimal
from django.db.models import Sum
import logging
import csv
from datetime import datetime

logger = logging.getLogger(__name__)

def _calculate_unpaid_amount_for_student(student, fee_types):
    """Calculate total unpaid amount for specified fee types using atomic calculator"""
    from core.fee_management.calculators import atomic_calculator
    
    if not fee_types:
        logger.debug(f"No fee types specified for student {student.admission_number}")
        return Decimal('0')
    
    # Get fee type IDs
    fee_type_ids = [ft.id for ft in fee_types]
    fee_type_names = [ft.display_format for ft in fee_types]
    
    # Use the enhanced method to check unpaid fees for specific fee types
    result = atomic_calculator.check_student_has_unpaid_fees_for_types(student, fee_type_ids)
    
    logger.info(f"Student {student.admission_number} unpaid check for fee types {fee_type_names}: ₹{result['unpaid_amount']} (eligible: {result['has_unpaid']})")
    
    return result['unpaid_amount']

@login_required
@csrf_protect
@module_required('fines', 'edit')
def add_fine(request):
    try:
        if request.method == 'POST':
            from .forms import FineForm
            form = FineForm(request.POST, request=request)
            form.initial['user'] = request.user
            if form.is_valid():
                fine = form.save(commit=False)
                fine.created_by = request.user
                fine.save()
                # Set M2M relationships before applying fine
                fees_group = form.cleaned_data.get('fees_group')
                fees_types = form.cleaned_data.get('fees_types')
                if fees_group:
                    fine.fees_group = fees_group
                    from fees.models import FeesType
                    group_fee_types = FeesType.objects.filter(fee_group=fees_group)
                    fine.fees_types.set(group_fee_types)
                elif fees_types:
                    fine.fees_types.set(fees_types)
                fine.save()
                # Apply fine to eligible students using improved logic
                from fines import utils as fines_utils
                application_result = fines_utils.apply_fine_to_eligible_students(
                    fine, form.cleaned_data
                )
                fine_students_created = application_result['eligible_count']
                ineligible_count = application_result['ineligible_count']
                logger.info(f"Fine application completed: {fine_students_created} eligible students, {ineligible_count} ineligible students")
                for eligible in application_result['eligible_students']:
                    student = eligible['student']
                    unpaid_amount = eligible['unpaid_amount']
                    logger.info(f"✅ Applied fine to {student.admission_number} with unpaid amount ₹{unpaid_amount}")
                for ineligible in application_result['ineligible_students']:
                    student = ineligible['student']
                    reason = ineligible['reason']
                    logger.info(f"⏭️ Skipped {student.admission_number}: {reason}")
                # Handle SMS notifications if checkbox is checked
                channels = request.POST.getlist('channels')
                if 'sms' in channels:
                    notification_result = fines_utils.send_fine_notifications(fine, request.user)
                    if notification_result.get('sent', 0) > 0:
                        messages.success(request, f"SMS notifications sent to {notification_result['sent']} students.")
                    if notification_result.get('failed', 0) > 0:
                        messages.warning(request, f"Failed to send SMS to {notification_result['failed']} students.")
                logger.info(f"User {request.user.id} created fine: {fine.fine_type.name} - ₹{fine.amount}")
                messages.success(request, f"Great! Fine '{fine.fine_type.name}' of ₹{fine.amount} has been applied successfully.")
                return redirect('fines:fine_history')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field.title()}: {error}")
        else:
            from .forms import FineForm
            form = FineForm()
        context = {'form': form}
        return render(request, 'fines/add_fine.html', context)
        
    except Exception as e:
        logger.error(f"Error in add_fine for user {request.user.id}: {str(e)}")
        messages.error(request, "We couldn't add the fine right now. Please try again.")
        from .forms import FineForm
        return render(request, 'fines/add_fine.html', {'form': FineForm()})

@login_required
@module_required('fines', 'view')
def fine_history(request):
    try:
        from .models import FineStudent, Fine
        from django.core.paginator import Paginator
        from django.db import models
        
        # Get search parameters
        search_query = request.GET.get('search', '')
        class_filter = request.GET.get('class_filter', '')
        status_filter = request.GET.get('status_filter', '')
        
        # Query fines directly with proper status filtering and fee group/type filters
        fines_qs = Fine.objects.select_related('fine_type', 'class_section').prefetch_related('fine_students').order_by('-applied_date')
        if search_query:
            fines_qs = fines_qs.filter(
                models.Q(class_section__class_name__icontains=search_query) |
                models.Q(class_section__section_name__icontains=search_query) |
                models.Q(fine_type__name__icontains=search_query) |
                models.Q(reason__icontains=search_query)
            )
        if class_filter:
            fines_qs = fines_qs.filter(class_section_id=class_filter)
        # Add fee group/type filters if present
        fee_group_filter = request.GET.get('fee_group_filter', '')
        fee_type_filter = request.GET.get('fee_type_filter', '')
        if fee_group_filter:
            fines_qs = fines_qs.filter(fees_group_id=fee_group_filter)
        if fee_type_filter:
            fines_qs = fines_qs.filter(fees_types__id=fee_type_filter)
        # Status filtering based on fine status
        if status_filter:
            if status_filter == 'active':
                fines_qs = fines_qs.filter(is_active=True)
            elif status_filter == 'deactivated':
                fines_qs = fines_qs.filter(is_active=False)
            elif status_filter == 'paid':
                from django.db.models import Count, Q
                fines_qs = fines_qs.annotate(
                    total_students=Count('fine_students'),
                    paid_students=Count('fine_students', filter=Q(fine_students__is_paid=True))
                ).filter(total_students__gt=0, total_students=models.F('paid_students'))
            elif status_filter == 'pending':
                fines_qs = fines_qs.filter(fine_students__is_paid=False).distinct()
        
        # Pagination
        paginator = Paginator(fines_qs, 25)
        page = request.GET.get('page', 1)
        page_obj = paginator.get_page(page)
        
        # Get available classes for filter dropdown
        from subjects.models import ClassSection
        from fees.models import FeesGroup, FeesType
        available_classes = ClassSection.objects.all().order_by('class_name', 'section_name')
        fee_groups = FeesGroup.objects.all().order_by('fee_group')
        fee_types = FeesType.objects.all().order_by('class_name')
        fee_group_filter = request.GET.get('fee_group_filter', '')
        fee_type_filter = request.GET.get('fee_type_filter', '')
        context = {
            'fines': page_obj,
            'page_obj': page_obj,
            'search_query': search_query,
            'class_filter': class_filter,
            'status_filter': status_filter,
            'available_classes': available_classes,
            'fee_groups': fee_groups,
            'fee_types': fee_types,
            'fee_group_filter': fee_group_filter,
            'fee_type_filter': fee_type_filter,
        }
        return render(request, 'fines/fine_history.html', context)
    except Exception as e:
        logger.error(f"Error in fine_history for user {request.user.id}: {str(e)}")
        messages.error(request, "We're having trouble loading the fine history. Please try again.")
        return render(request, 'fines/fine_history.html')

@login_required
@require_POST
@csrf_protect
@module_required('fines', 'edit')
def deactivate_fine(request, fine_id):
    try:
        from core.fee_management.services import fee_service
        
        # Validate fine ID
        fine_id_int = int(fine_id)
        if fine_id_int < 0:
            raise ValidationError("Invalid fine ID")
        
        # Deactivate fine using service
        result = fee_service.deactivate_fine(fine_id_int, request.user)
        
        if result['success']:
            messages.success(request, result['message'])
        else:
            messages.error(request, f"Error: {result['error']}")
        
    except (ValueError, ValidationError):
        messages.error(request, "Invalid fine information. Please try again.")
    except Exception as e:
        logger.error(f"Error deactivating fine {fine_id} by user {request.user.id}: {str(e)}")
        messages.error(request, "We couldn't deactivate the fine right now. Please try again.")
    
    return redirect('fines:fine_history')

@login_required
@require_POST
@csrf_protect
@module_required('fines', 'edit')
def waive_fines(request):
    try:
        from .forms import FineWaiverForm
        from . import utils as fines_utils

        fine_ids_raw = request.POST.get('fine_ids', '')
        waiver_reason = request.POST.get('waiver_reason', '').strip()
        fine_student_ids = []
        if fine_ids_raw:
            for part in fine_ids_raw.split(','):
                part = part.strip()
                if part.isdigit():
                    fine_student_ids.append(int(part))
        if fine_student_ids and waiver_reason:
            result = fines_utils.waive_fine_students(fine_student_ids, waiver_reason, request.user)
            if result.get('success'):
                messages.success(request, result.get('message', 'Fines waived'))
                for err in result.get('errors', []):
                    messages.warning(request, err)
            else:
                messages.error(request, 'Some errors occurred while waiving fines')
                for err in result.get('errors', []):
                    messages.warning(request, err)
        else:
            messages.error(request, 'Please select fines and provide a waiver reason.')
        
    except Exception as e:
        logger.error(f"Error waiving fines by user {request.user.id}: {str(e)}")
        messages.error(request, "We couldn't waive the fines right now. Please try again.")
    
    return redirect('fines:fine_history')

@login_required
@require_POST
@csrf_protect
@module_required('fines', 'edit')
def delete_fine(request, fine_id):
    try:
        from .models import Fine
        from django.shortcuts import get_object_or_404
        
        # Validate fine ID
        fine_id_int = int(fine_id)
        if fine_id_int < 0:
            raise ValidationError("Invalid fine ID")
        
        # Get the fine object
        fine = get_object_or_404(Fine, id=fine_id_int)
        fine_info = f"{fine.fine_type.name} (₹{fine.amount})"
        
        # Log the deletion attempt
        logger.info(f"User {request.user.id} attempting to delete fine {fine_id_int}: {fine_info}")
        
        # Delete the fine (this will cascade delete FineStudent records)
        fine.delete()
        
        messages.success(request, f"Perfect! Fine '{fine_info}' has been removed successfully.")
        
    except (ValueError, ValidationError):
        messages.error(request, "Invalid fine information. Please try again.")
    except Exception as e:
        logger.error(f"Error deleting fine {fine_id} by user {request.user.id}: {str(e)}")
        messages.error(request, "We couldn't remove the fine right now. Please try again.")
    
    return redirect('fines:fine_history')

@module_required('fines', 'edit')
def upload_fines(request):
    return render(request, 'fines/upload_fines.html')

@module_required('fines', 'view')
def base_fine(request):
    return render(request, 'fines/base_fine.html')

@login_required
@csrf_protect
@module_required('fines', 'edit')
def edit_fine(request, fine_id):
    try:
        from .models import Fine
        from .forms import FineForm
        
        fine = get_object_or_404(Fine, id=fine_id)
        
        if request.method == 'POST':
            form = FineForm(request.POST, instance=fine, request=request)
            if form.is_valid():
                fine = form.save(commit=False)
                fine.save()
                logger.info(f"User {request.user.id} updated fine: {fine.fine_type.name} - 9{fine.amount}")
                messages.success(request, f"Perfect! Fine '{fine.fine_type.name}' has been updated successfully.")
                return redirect('fines:fine_history')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field.title()}: {error}")
        else:
            initial = {
                'fees_group': fine.fees_group,
                'fees_types': fine.fees_types.all(),
                'class_section': fine.class_section,
                'students': fine.students.all(),
            }
            form = FineForm(instance=fine, initial=initial)
        context = {
            'form': form,
            'fine': fine
        }
        return render(request, 'fines/edit_fine.html', context)
        
    except Exception as e:
        logger.error(f"Error in edit_fine {fine_id} for user {request.user.id}: {str(e)}")
        messages.error(request, "We couldn't load the fine for editing. Please try again.")
        return redirect('fines:fine_history')

@module_required('fines', 'view')
def fine_types(request):
    try:
        from .models import FineType
        
        # Query fine types
        fine_types = FineType.objects.all().order_by('-created_at')
        
        context = {
            'fine_types': fine_types,
        }
        
        return render(request, 'fines/fine_types.html', context)
    except Exception as e:
        logger.error(f"Error in fine_types for user {request.user.id}: {str(e)}")
        messages.error(request, "We're having trouble loading the fine types. Please try again.")
        return render(request, 'fines/fine_types.html')

@login_required
@csrf_protect
@module_required('fines', 'edit')
def add_fine_type(request):
    try:
        if request.method == 'POST':
            from .forms import FineTypeForm
            form = FineTypeForm(request.POST)
            
            if form.is_valid():
                fine_type = form.save(commit=False)
                fine_type.created_by = request.user
                fine_type.save()
                
                logger.info(f"User {request.user.id} created fine type: {fine_type.name}")
                messages.success(request, f"Great! Fine type '{fine_type.name}' has been created successfully.")
                return redirect('fines:fine_types')
            else:
                # Form has validation errors
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field.title()}: {error}")
        else:
            from .forms import FineTypeForm
            form = FineTypeForm()
        
        context = {'form': form}
        return render(request, 'fines/add_fine_type.html', context)
        
    except Exception as e:
        logger.error(f"Error in add_fine_type for user {request.user.id}: {str(e)}")
        messages.error(request, "We couldn't create the fine type right now. Please try again.")
        return render(request, 'fines/add_fine_type.html', {'form': FineTypeForm()})

@login_required
@csrf_protect
@module_required('fines', 'edit')
def edit_fine_type(request, fine_type_id):
    try:
        from .models import FineType
        from .forms import FineTypeForm
        from django.shortcuts import get_object_or_404
        
        fine_type = get_object_or_404(FineType, id=fine_type_id)
        
        if request.method == 'POST':
            form = FineTypeForm(request.POST, instance=fine_type)
            
            if form.is_valid():
                fine_type = form.save(commit=False)
                fine_type.updated_by = request.user
                fine_type.save()
                
                logger.info(f"User {request.user.id} updated fine type: {fine_type.name}")
                messages.success(request, f"Perfect! Fine type '{fine_type.name}' has been updated successfully.")
                return redirect('fines:fine_types')
            else:
                # Form has validation errors
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field.title()}: {error}")
        else:
            form = FineTypeForm(instance=fine_type)
        
        context = {
            'form': form,
            'fine_type': fine_type
        }
        return render(request, 'fines/edit_fine_type.html', context)
        
    except Exception as e:
        logger.error(f"Error in edit_fine_type {fine_type_id} for user {request.user.id}: {str(e)}")
        messages.error(request, "We couldn't load the fine type for editing. Please try again.")
        return redirect('fines:fine_types')

@login_required
@require_POST
@csrf_protect
@module_required('fines', 'edit')
def toggle_fine_type_status(request, fine_type_id):
    try:
        from .models import FineType
        from django.shortcuts import get_object_or_404
        
        fine_type = get_object_or_404(FineType, id=fine_type_id)
        fine_type.is_active = not fine_type.is_active
        fine_type.save()
        
        status = "activated" if fine_type.is_active else "deactivated"
        logger.info(f"User {request.user.id} {status} fine type: {fine_type.name}")
        
        return JsonResponse({
            'status': 'success',
            'message': f"Perfect! Fine type '{fine_type.name}' has been {status} successfully.",
            'is_active': fine_type.is_active
        })
        
    except Exception as e:
        logger.error(f"Error toggling fine type status {fine_type_id} by user {request.user.id}: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': "We couldn't update the fine type status right now. Please try again."
        }, status=500)

@login_required
@require_POST
@csrf_protect
@module_required('fines', 'edit')
def delete_fine_type(request, fine_type_id):
    try:
        from .models import FineType, Fine
        from django.shortcuts import get_object_or_404
        
        # Validate fine type ID
        fine_type_id_int = int(fine_type_id)
        if fine_type_id_int < 0:
            raise ValidationError("Invalid fine type ID")
        
        # Get the fine type object
        fine_type = get_object_or_404(FineType, id=fine_type_id_int)
        fine_type_name = fine_type.name
        
        # Check if fine type is being used
        active_fines = Fine.objects.filter(fine_type=fine_type).count()
        if active_fines > 0:
            messages.error(request, f"Cannot delete '{fine_type_name}' because it's being used by {active_fines} active fine(s). Please remove those fines first.")
            return redirect('fines:fine_types')
        
        # Log the deletion attempt
        logger.info(f"User {request.user.id} attempting to delete fine type {fine_type_id_int}: {fine_type_name}")
        
        # Delete the fine type
        fine_type.delete()
        
        messages.success(request, f"Perfect! Fine type '{fine_type_name}' has been removed successfully.")
        
    except (ValueError, ValidationError):
        messages.error(request, "Invalid fine type information. Please try again.")
    except Exception as e:
        logger.error(f"Error deleting fine type {fine_type_id} by user {request.user.id}: {str(e)}")
        messages.error(request, "We couldn't remove the fine type right now. Please try again.")
    
    return redirect('fines:fine_types')

@login_required
@module_required('fines', 'view')
def load_students_for_class(request):
    try:
        from students.models import Student
        
        class_id = request.GET.get('class_id')
        if class_id:
            try:
                class_id_int = int(class_id)
                if class_id_int < 0:
                    return JsonResponse({'error': 'Invalid class ID'}, status=400)
                
                # Load students for the specific class
                students = Student.objects.filter(class_section_id=class_id_int).select_related('class_section')
                student_data = []
                for student in students:
                    student_data.append({
                        'id': student.id,
                        'name': f"{student.first_name} {student.last_name}",
                        'admission_number': student.admission_number,
                        'class_name': f"{student.class_section.class_name}{student.class_section.section_name}" if student.class_section else 'N/A',
                        'father_name': getattr(student, 'father_name', 'N/A')
                    })
                
                return JsonResponse({
                    'students': student_data,
                    'status': 'success'
                })
            except (ValueError, TypeError):
                return JsonResponse({'error': 'Invalid class ID format'}, status=400)
        
        return JsonResponse({'students': [], 'status': 'success'})
    except Exception as e:
        logger.error(f"Error loading students for class by user {request.user.id}: {str(e)}")
        return JsonResponse({'error': 'Unable to load students'}, status=500)

@login_required
@module_required('fines', 'view')
def load_fees_types(request):
    try:
        fees_group_id = request.GET.get('fees_group_id')
        if fees_group_id:
            from fees.models import FeesType
            fees_types = FeesType.objects.filter(fee_group_id=fees_group_id).select_related('fee_group')
            
            fees_types_data = []
            for ft in fees_types:
                fees_types_data.append({
                    'id': ft.id,
                    'group_type': ft.group_type,  # This is a property
                    'fee_type': ft.fee_type,      # This is a property
                    'amount': str(ft.amount),
                    'amount_type': ft.amount_type,
                    'class_name': ft.class_name or '',
                    'month_name': ft.month_name or '',
                    'stoppage_name': ft.stoppage_name or '',
                    'display_format': ft.display_format,
                    'description': f"{ft.fee_group.group_type} - {ft.amount_type} (₹{ft.amount})"
                })
            
            return JsonResponse({
                'fees_types': fees_types_data,
                'status': 'success'
            })
        return JsonResponse({'fees_types': [], 'status': 'success'})
    except Exception as e:
        logger.error(f"Error loading fees types: {str(e)}")
        return JsonResponse({'error': 'Unable to load fees types'}, status=500)

@login_required
@module_required('fines', 'view')
def load_classes_for_fees_type(request):
    try:
        from subjects.models import ClassSection
        classes = ClassSection.objects.all().values('id', 'class_name', 'section_name')
        return JsonResponse({
            'classes': [{'id': c['id'], 'name': f"{c['class_name']}{c['section_name']}"} for c in classes],
            'status': 'success'
        })
    except Exception as e:
        logger.error(f"Error loading classes: {str(e)}")
        return JsonResponse({'error': 'Unable to load classes'}, status=500)

@login_required
@module_required('fines', 'view')
def load_students_for_fees_type(request):
    try:
        from students.models import Student
        students = Student.objects.select_related('class_section').all()[:100]  # Limit for performance
        student_data = []
        for student in students:
            student_data.append({
                'id': student.id,
                'name': f"{student.first_name} {student.last_name}",
                'admission_number': student.admission_number,
                'class_name': f"{student.class_section.class_name}{student.class_section.section_name}" if student.class_section else 'N/A',
                'father_name': getattr(student, 'father_name', 'N/A')
            })
        return JsonResponse({
            'students': student_data,
            'status': 'success'
        })
    except Exception as e:
        logger.error(f"Error loading students: {str(e)}")
        return JsonResponse({'error': 'Unable to load students'}, status=500)

@login_required
@module_required('fines', 'view')
def search_students(request):
    try:
        from students.models import Student
        from django.db.models import Q
        
        search_term = request.GET.get('q', '').strip()
        if search_term and len(search_term) >= 2:
            # Search students by name, admission number, or father name
            students = Student.objects.select_related('class_section').filter(
                Q(first_name__icontains=search_term) |
                Q(last_name__icontains=search_term) |
                Q(admission_number__icontains=search_term) |
                Q(father_name__icontains=search_term)
            )[:50]  # Limit results
            
            student_data = []
            for student in students:
                student_data.append({
                    'id': student.id,
                    'name': f"{student.first_name} {student.last_name}",
                    'admission_number': student.admission_number,
                    'class_name': f"{student.class_section.class_name}{student.class_section.section_name}" if student.class_section else 'N/A',
                    'father_name': getattr(student, 'father_name', 'N/A')
                })
            
            return JsonResponse({
                'students': student_data,
                'status': 'success'
            })
        
        return JsonResponse({'students': [], 'status': 'success'})
    except Exception as e:
        logger.error(f"Error searching students by user {request.user.id}: {str(e)}")
        return JsonResponse({'error': 'Search unavailable'}, status=500)

@login_required
@module_required('fines', 'view')
def download_sample_csv(request):
    try:
        # Log the download attempt
        logger.info(f"User {request.user.id} downloading sample CSV")
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="sample_fines.csv"'
        response['Content-Security-Policy'] = "default-src 'none'"
        
        # Add sample CSV content
        response.write('Student Name,Admission Number,Fine Amount,Reason\n')
        response.write('John Doe,ADM001,100,Late submission\n')
        
        return response
    except Exception as e:
        logger.error(f"Error downloading sample CSV by user {request.user.id}: {str(e)}")
        return HttpResponse('Error generating sample file', status=500)

@login_required
@module_required('fines', 'view')
def get_fine_type_usage(request, fine_type_id):
    try:
        from .models import FineType, Fine
        from django.shortcuts import get_object_or_404
        
        # Validate fine type ID
        try:
            type_id_int = int(fine_type_id)
            if type_id_int < 0:
                return JsonResponse({'error': 'Invalid fine type ID'}, status=400)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid fine type ID format'}, status=400)
        
        # Get the fine type and count usage
        fine_type = get_object_or_404(FineType, id=type_id_int)
        usage_count = Fine.objects.filter(fine_type=fine_type).count()
        
        return JsonResponse({
            'usage': usage_count,
            'status': 'success',
            'fine_type_name': fine_type.name,
            'can_delete': usage_count == 0
        })
    except Exception as e:
        logger.error(f"Error getting fine type usage {fine_type_id} by user {request.user.id}: {str(e)}")
        return JsonResponse({'error': 'Usage data unavailable'}, status=500)

@login_required
@module_required('fines', 'view')
def get_fee_types_for_group(request):
    """AJAX endpoint to get fee types for selected fee group"""
    try:
        fees_group_id = request.GET.get('fees_group_id')
        if fees_group_id:
            from fees.models import FeesType
            fee_types = FeesType.objects.filter(fee_group_id=fees_group_id).select_related('fee_group')
            
            fee_types_data = []
            for ft in fee_types:
                fee_types_data.append({
                    'id': ft.id,
                    'name': ft.display_format,
                    'amount': str(ft.amount),
                    'description': f"{ft.fee_group.group_type} - {ft.amount_type}"
                })
            
            return JsonResponse({
                'fee_types': fee_types_data,
                'status': 'success'
            })
        
        return JsonResponse({'fee_types': [], 'status': 'success'})
    except Exception as e:
        logger.error(f"Error loading fee types for group: {str(e)}")
        return JsonResponse({'error': 'Unable to load fee types'}, status=500)

@login_required
@module_required('fines', 'view')
def get_classes_for_fee_types(request):
    """AJAX endpoint to get applicable classes for selected fee types"""
    try:
        fee_type_ids = request.GET.getlist('fee_type_ids[]')
        if fee_type_ids:
            from fees.models import FeesType
            from subjects.models import ClassSection
            
            # Get fee types
            fee_types = FeesType.objects.filter(id__in=fee_type_ids)
            
            # Get applicable classes
            applicable_classes = set()
            for ft in fee_types:
                if ft.class_name:
                    # Fee type is class-specific
                    class_sections = ClassSection.objects.filter(class_name__iexact=ft.class_name)
                    applicable_classes.update(class_sections)
                else:
                    # Fee type applies to all classes
                    applicable_classes.update(ClassSection.objects.all())
            
            classes_data = []
            for cs in applicable_classes:
                classes_data.append({
                    'id': cs.id,
                    'name': cs.display_name
                })
            
            return JsonResponse({
                'classes': sorted(classes_data, key=lambda x: x['name']),
                'status': 'success'
            })
        
        return JsonResponse({'classes': [], 'status': 'success'})
    except Exception as e:
        logger.error(f"Error loading classes for fee types: {str(e)}")
        return JsonResponse({'error': 'Unable to load classes'}, status=500)

@login_required
@module_required('fines', 'view')
def export_fines_csv(request):
    """Export fines data to CSV format"""
    try:
        import csv
        from datetime import datetime
        
        # Log the export attempt
        logger.info(f"User {request.user.id} exporting fines CSV")
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="fines_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        response['Content-Security-Policy'] = "default-src 'none'"
        
        writer = csv.writer(response)
        
        # Write CSV headers
        writer.writerow([
            'Student Name',
            'Admission Number', 
            'Class',
            'Fine Type',
            'Amount (₹)',
            'Due Date',
            'Status',
            'Applied Date',
            'Reason'
        ])
        
        # Sample data - in real implementation, this would fetch from database
        sample_data = [
            ['John Doe', 'ADM001', '10-A', 'Late Fee', '100', '2024-01-15', 'Pending', '2024-01-10', 'Late submission'],
            ['Jane Smith', 'ADM002', '9-B', 'Uniform Fine', '50', '2024-01-20', 'Paid', '2024-01-12', 'Improper uniform'],
        ]
        
        for row in sample_data:
            writer.writerow(row)
        
        messages.success(request, "Great! Fines data has been exported successfully.")
        return response
        
    except Exception as e:
        logger.error(f"Error exporting fines CSV by user {request.user.id}: {str(e)}")
        messages.error(request, "We couldn't export the data right now. Please try again.")
        return redirect('fines:fine_history')

@login_required
@module_required('fines', 'view')
def verify_fine_application(request, fine_id):
    """Verify that fine was applied correctly to intended students"""
    try:
        from core.fee_management.services import fee_service
        
        verification = fee_service.verify_fine_application(fine_id)
        
        if 'error' in verification:
            messages.error(request, f"Error verifying fine: {verification['error']}")
            return redirect('fines:fine_history')
        
        context = {
            'verification': verification,
            'fine_id': fine_id
        }
        
        return render(request, 'fines/verify_fine.html', context)
        
    except Exception as e:
        logger.error(f"Error verifying fine {fine_id} by user {request.user.id}: {str(e)}")
        messages.error(request, "We couldn't verify the fine application. Please try again.")
        return redirect('fines:fine_history')

@login_required
@require_POST
@csrf_protect
@module_required('fines', 'edit')
def fix_fine_application(request, fine_id):
    """Fix incorrectly applied fine by removing from wrong classes"""
    try:
        from core.fee_management.services import fee_service
        
        result = fee_service.fix_incorrect_fine_application(fine_id)
        
        if result['success']:
            messages.success(request, result['message'])
            logger.info(f"User {request.user.id} fixed fine application {fine_id}: {result['message']}")
        else:
            messages.error(request, f"Error fixing fine: {result['error']}")
        
    except Exception as e:
        logger.error(f"Error fixing fine application {fine_id} by user {request.user.id}: {str(e)}")
        messages.error(request, "We couldn't fix the fine application. Please try again.")
    
    return redirect('fines:fine_history')

@login_required
@module_required('fines', 'view')
def analyze_fee_type(request, fees_type_id):
    """Analyze fee type payment status across all classes"""
    try:
        from core.fee_management.services import fee_service
        
        analysis = fee_service.get_fee_type_analysis(fees_type_id)
        
        if 'error' in analysis:
            messages.error(request, f"Error analyzing fee type: {analysis['error']}")
            return redirect('fines:fine_history')
        
        context = {
            'analysis': analysis,
            'fees_type_id': fees_type_id
        }
        
        return render(request, 'fines/analyze_fee_type.html', context)
        
    except Exception as e:
        logger.error(f"Error analyzing fee type {fees_type_id} by user {request.user.id}: {str(e)}")
        messages.error(request, "We couldn't analyze the fee type. Please try again.")
        return redirect('fines:fine_history')