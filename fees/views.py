from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.utils.html import escape
from django.db import models
from users.decorators import module_required
from core.exports import ExportService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@login_required
@module_required('fees', 'view')
def fees_setup(request):
    try:
        from .models import FeesType, FeesGroup
        from django.core.paginator import Paginator
        
        # Get search parameters
        search_query = request.GET.get('q', '')
        amount_type = request.GET.get('amount_type', '')
        amount = request.GET.get('amount', '')
        page_size = int(request.GET.get('page_size', 25))
        
        # Query fee types
        fee_types_qs = FeesType.objects.all().order_by('-created_at')
        if search_query:
            fee_types_qs = fee_types_qs.filter(
                models.Q(fee_type__icontains=search_query) |
                models.Q(group_type__icontains=search_query)
            )
        if amount_type:
            fee_types_qs = fee_types_qs.filter(amount_type__icontains=amount_type)
        if amount:
            fee_types_qs = fee_types_qs.filter(amount=amount)
        
        # Query fee groups
        fee_groups_qs = FeesGroup.objects.all().order_by('-created_at')
        
        # Pagination
        fee_types_paginator = Paginator(fee_types_qs, page_size)
        fee_groups_paginator = Paginator(fee_groups_qs, page_size)
        
        page = request.GET.get('page', 1)
        type_page = request.GET.get('type_page', 1)
        
        fee_types = fee_types_paginator.get_page(page)
        fee_groups = fee_groups_paginator.get_page(type_page)
        
        context = {
            'fee_types': fee_types,
            'fee_groups': fee_groups,
            'search_query': search_query,
            'page_size': page_size,
        }
        
        return render(request, 'fees/fees_setup.html', context)
    except Exception as e:
        logger.error(f"Error in fees_setup for user {request.user.id}: {str(e)}")
        messages.error(request, "We're having trouble loading the fees setup. Please try again.")
        return render(request, 'fees/fees_setup.html')

@login_required
@module_required('fees', 'view')
def load_group_types(request):
    try:
        # Validate request method
        if request.method not in ['GET', 'POST']:
            return JsonResponse({'error': 'Invalid request method'}, status=405)
        
        # Return sanitized data
        return JsonResponse({'types': [], 'status': 'success'})
    except Exception as e:
        logger.error(f"Error loading group types for user {request.user.id}: {str(e)}")
        return JsonResponse({'error': 'Unable to load group types'}, status=500)

@login_required
@csrf_protect
@module_required('fees', 'edit')
def add_fees_group(request):
    try:
        from .forms import FeesGroupForm
        from .models import FeesGroup
        
        if request.method == 'POST':
            form = FeesGroupForm(request.POST)
            if form.is_valid():
                fee_group = form.save()
                messages.success(request, f"Great! Fee group '{fee_group.fee_group} - {fee_group.group_type}' has been created successfully.")
                return redirect('fees:fees_setup')
            else:
                messages.error(request, "Please correct the errors below and try again.")
        else:
            form = FeesGroupForm()
        
        return render(request, 'fees/add_fees_group.html', {'form': form})
    except Exception as e:
        logger.error(f"Error in add_fees_group for user {request.user.id}: {str(e)}")
        messages.error(request, "We couldn't create the fee group right now. Please try again.")
        return render(request, 'fees/add_fees_group.html', {'form': FeesGroupForm()})

@login_required
@csrf_protect
@module_required('fees', 'edit')
def edit_fees_group(request, pk):
    try:
        from .forms import FeesGroupForm
        from .models import FeesGroup
        
        fee_group = FeesGroup.objects.get(id=pk)
        
        if request.method == 'POST':
            form = FeesGroupForm(request.POST, instance=fee_group)
            if form.is_valid():
                updated_group = form.save()
                messages.success(request, f"Perfect! Fee group '{updated_group.fee_group} - {updated_group.group_type}' has been updated successfully.")
                return redirect('fees:fees_setup')
            else:
                messages.error(request, "Please correct the errors below and try again.")
        else:
            form = FeesGroupForm(instance=fee_group)
        
        return render(request, 'fees/edit_fees_group.html', {'form': form, 'fee_group': fee_group})
    except FeesGroup.DoesNotExist:
        messages.error(request, "Fee group not found.")
        return redirect('fees:fees_setup')
    except Exception as e:
        logger.error(f"Error in edit_fees_group for ID {pk} by user {request.user.id}: {str(e)}")
        messages.error(request, "We couldn't load the group details. Please try again.")
        return redirect('fees:fees_setup')

@login_required
@require_POST
@csrf_protect
@module_required('fees', 'edit')
def delete_fees_group(request, pk):
    try:
        # Validate primary key
        group_id = int(pk)
        if group_id < 0:
            raise ValidationError("Invalid group ID")
        
        # Log the deletion attempt
        logger.info(f"User {request.user.id} attempting to delete fee group {group_id}")
        
        # Actual deletion logic
        from .models import FeesGroup
        fee_group = FeesGroup.objects.get(id=group_id)
        group_name = fee_group.fee_group
        fee_group.delete()
        messages.success(request, f"Perfect! Fee group '{group_name}' has been removed successfully.")
        
    except (ValueError, ValidationError):
        messages.error(request, "Invalid group information. Please try again.")
    except Exception as e:
        logger.error(f"Error deleting fee group {pk} by user {request.user.id}: {str(e)}")
        messages.error(request, "We couldn't remove the fee group right now. Please try again.")
    
    return redirect('fees:fees_setup')

@login_required
@csrf_protect
@module_required('fees', 'edit')
def add_fees_type(request):
    try:
        from .forms import DynamicFeesTypeForm
        from .models import FeesType, FeesGroup
        
        if request.method == 'POST':
            form = DynamicFeesTypeForm(request.POST)
            if form.is_valid():
                # Create multiple fee type instances based on context
                created_fees = []
                cleaned_data = form.cleaned_data
                
                context_type = cleaned_data['context_type']
                context_data = cleaned_data['context_data']
                fee_group = cleaned_data['fee_group']
                amount = cleaned_data['amount']
                amount_type = cleaned_data['amount_type']  # USER INPUT
                
                if context_type == 'monthly':
                    # For monthly fees, also check if classes are selected
                    selected_classes = cleaned_data.get('selected_classes', [])
                    
                    # Check if fee group requires classes or stoppages
                    requires_classes = fee_group.fee_type == 'Class Based'
                    requires_stoppages = fee_group.fee_type == 'Stoppage Based'
                    selected_stoppages = cleaned_data.get('selected_stoppages', [])
                    
                    if selected_classes or requires_classes:
                        # If no classes selected but required, use default classes
                        if not selected_classes and requires_classes:
                            try:
                                from subjects.models import ClassSection
                                default_classes = ClassSection.objects.all()[:2]  # Get first 2 classes
                                selected_classes = [cs.display_name for cs in default_classes]
                            except:
                                selected_classes = ['Class 10A', 'Class 9B']  # Fallback
                        
                        # Create fee for each month-class combination
                        for month in context_data['months']:
                            for class_name in selected_classes:
                                fee_type = FeesType.objects.create(
                                    fee_group=fee_group,
                                    amount=amount,
                                    amount_type=month,  # Use individual month instead of combined
                                    context_type='class_based' if requires_classes else context_type,
                                    context_data={'months': [month], 'classes': [class_name]},
                                    month_name=month,
                                    class_name=class_name
                                )
                                created_fees.append(fee_type)
                    
                    elif selected_stoppages or requires_stoppages:
                        # Convert stoppage IDs to names if needed
                        if selected_stoppages and all(str(s).isdigit() for s in selected_stoppages):
                            try:
                                from transport.models import Stoppage
                                stoppage_names = [Stoppage.objects.get(id=int(s_id)).name for s_id in selected_stoppages]
                            except:
                                stoppage_names = selected_stoppages
                        else:
                            stoppage_names = selected_stoppages
                        
                        # If no stoppages selected but required, use defaults
                        if not stoppage_names and requires_stoppages:
                            try:
                                from transport.models import Stoppage
                                default_stoppages = Stoppage.objects.all()[:2]
                                stoppage_names = [s.name for s in default_stoppages]
                            except:
                                stoppage_names = ['Default Stoppage']
                        
                        # Create fee for each month-stoppage combination
                        for month in context_data['months']:
                            for stoppage_name in stoppage_names:
                                # Get the related stoppage object
                                related_stoppage = None
                                try:
                                    from transport.models import Stoppage
                                    related_stoppage = Stoppage.objects.filter(name=stoppage_name).first()
                                except:
                                    pass
                                
                                fee_type = FeesType.objects.create(
                                    fee_group=fee_group,
                                    amount=amount,
                                    amount_type=month,  # Use individual month instead of combined
                                    context_type='stoppage_based',
                                    context_data={'months': [month], 'stoppages': [stoppage_name]},
                                    month_name=month,
                                    stoppage_name=stoppage_name,
                                    related_stoppage=related_stoppage
                                )
                                created_fees.append(fee_type)
                    else:
                        # Create separate fee type for each month only
                        for month in context_data['months']:
                            fee_type = FeesType.objects.create(
                                fee_group=fee_group,
                                amount=amount,
                                amount_type=month,  # Use individual month instead of combined
                                context_type=context_type,
                                context_data={'months': [month]},
                                month_name=month
                            )
                            created_fees.append(fee_type)
                
                elif context_type in ['class_based', 'stoppage_based']:
                    # Create separate fee type for each class/stoppage
                    items = context_data.get('classes', []) or context_data.get('stoppages', [])
                    
                    # If no items provided but context requires them, use defaults
                    if not items and context_type == 'class_based':
                        try:
                            from subjects.models import ClassSection
                            default_classes = ClassSection.objects.all()[:2]
                            items = [cs.display_name for cs in default_classes]
                        except:
                            items = ['Class 10A', 'Class 9B']  # Fallback
                    elif not items and context_type == 'stoppage_based':
                        try:
                            from transport.models import Stoppage
                            default_stoppages = Stoppage.objects.all()[:2]
                            items = [s.name for s in default_stoppages]
                        except:
                            items = ['Default Stoppage']  # Fallback
                    
                    for item in items:
                        extra_fields = {}
                        if context_type == 'class_based':
                            # Find the actual ClassSection object
                            try:
                                from subjects.models import ClassSection
                                class_section = ClassSection.objects.filter(display_name=item).first()
                                if class_section:
                                    extra_fields['class_name'] = class_section.display_name
                                else:
                                    extra_fields['class_name'] = item
                            except:
                                extra_fields['class_name'] = item
                        elif context_type == 'stoppage_based':
                            # item is already the stoppage name from context_data
                            extra_fields['stoppage_name'] = item
                            # Also set the related_stoppage if available
                            try:
                                from transport.models import Stoppage
                                stoppage = Stoppage.objects.filter(name=item).first()
                                if stoppage:
                                    extra_fields['related_stoppage'] = stoppage
                            except:
                                pass
                            
                        fee_type = FeesType.objects.create(
                            fee_group=fee_group,
                            amount=amount,
                            amount_type=amount_type,  # USER INPUT
                            context_type=context_type,
                            context_data={context_type.split('_')[0] + 's': [item]},
                            **extra_fields
                        )
                        created_fees.append(fee_type)
                
                else:
                    # Create single fee type for general fees
                    fee_type = FeesType.objects.create(
                        fee_group=fee_group,
                        amount=amount,
                        amount_type=amount_type,  # USER INPUT
                        context_type=context_type,
                        context_data=context_data
                    )
                    created_fees.append(fee_type)
                
                count = len(created_fees)
                if count == 1:
                    messages.success(
                        request, 
                        f"Great! Fee type created successfully: {created_fees[0].display_format}"
                    )
                else:
                    fee_list = [fee.display_format for fee in created_fees[:3]]  # Show first 3
                    if count > 3:
                        fee_list.append(f"... and {count - 3} more")
                    messages.success(
                        request, 
                        f"Excellent! {count} fee types created successfully. Examples: {', '.join(fee_list)}"
                    )
                return redirect('fees:fees_setup')
            else:
                messages.error(request, "Please correct the errors below and try again.")
        else:
            form = DynamicFeesTypeForm()
        
        # Get context data for template
        fee_groups = FeesGroup.objects.all().order_by('fee_group', 'group_type')
        
        try:
            from subjects.models import ClassSection
            class_sections = ClassSection.objects.all().order_by('class_name', 'section_name')
            logger.info(f"Found {class_sections.count()} class sections for add_fees_type")
        except Exception as e:
            logger.error(f"Error loading ClassSection: {str(e)}")
            class_sections = []
            
        try:
            from transport.models import Stoppage
            stoppages = Stoppage.objects.all().order_by('name')
        except Exception:
            stoppages = []
        
        # Preserve form values if there are errors
        preserved_values = {}
        if request.method == 'POST' and not form.is_valid():
            preserved_values = {
                'fee_group': request.POST.get('fee_group', ''),
                'amount_type': request.POST.get('amount_type', ''),
                'amount': request.POST.get('amount', ''),
                'custom_fee_name': request.POST.get('custom_fee_name', ''),
                'selected_classes': request.POST.getlist('selected_classes'),
                'selected_stoppages': request.POST.getlist('selected_stoppages'),
                'selected_months': request.POST.getlist('selected_months'),
            }
        
        context = {
            'form': form,
            'fee_groups': fee_groups,
            'class_sections': class_sections,
            'stoppages': stoppages,
            'preserved_values': preserved_values
        }
        
        return render(request, 'fees/add_fees_type.html', context)
        
    except Exception as e:
        logger.error(f"Error in add_fees_type for user {request.user.id}: {str(e)}")
        messages.error(request, "We couldn't create the fee type right now. Please try again.")
        return render(request, 'fees/add_fees_type.html', {'form': DynamicFeesTypeForm(), 'fee_groups': []})

@login_required
@csrf_protect
@module_required('fees', 'edit')
def edit_fees_type(request, pk):
    try:
        from .forms import DynamicFeesTypeForm
        from .models import FeesType, FeesGroup

        logger.info(f"User {request.user.id} attempting to edit FeesType id={pk} with method {request.method}")
        fee_type = FeesType.objects.get(id=pk)

        if request.method == 'POST':
            logger.info(f"POST data: {request.POST}")
            form = DynamicFeesTypeForm(request.POST, instance=fee_type)
            if form.is_valid():
                logger.info(f"Form valid for FeesType id={pk}. Cleaned data: {form.cleaned_data}")
                updated_fee_type = form.save()
                logger.info(f"FeesType id={pk} updated successfully by user {request.user.id}")
                messages.success(request, f"Perfect! Fee type '{updated_fee_type.amount_type}' has been updated successfully.")
                return redirect('fees:fees_setup')
            else:
                logger.warning(f"Form invalid for FeesType id={pk}. Errors: {form.errors}")
                messages.error(request, "Please correct the errors below and try again.")
        else:
            logger.info(f"Rendering edit form for FeesType id={pk}")
            form = DynamicFeesTypeForm(instance=fee_type)

        # Get fee groups for the template
        fee_groups = FeesGroup.objects.all().order_by('fee_group', 'group_type')

        try:
            from subjects.models import ClassSection
            class_sections = ClassSection.objects.all().order_by('class_name', 'section_name')
        except Exception as e:
            logger.warning(f"Error loading ClassSection for edit_fees_type: {str(e)}")
            class_sections = []

        try:
            from transport.models import Stoppage
            stoppages = Stoppage.objects.all().order_by('name')
        except Exception as e:
            logger.warning(f"Error loading Stoppage for edit_fees_type: {str(e)}")
            stoppages = []

        context = {
            'form': form,
            'fee_type': fee_type,
            'fee_groups': fee_groups,
            'class_sections': class_sections,
            'stoppages': stoppages
        }

        logger.info(f"Rendering edit_fees_type.html for FeesType id={pk} with context: {context}")
        return render(request, 'fees/edit_fees_type.html', context)
    except FeesType.DoesNotExist:
        logger.error(f"FeesType id={pk} not found for user {request.user.id}")
        messages.error(request, "Fee type not found.")
        return redirect('fees:fees_setup')
    except Exception as e:
        logger.error(f"Error in edit_fees_type for ID {pk} by user {request.user.id}: {str(e)}")
        messages.error(request, "We couldn't load the fee type details. Please try again.")
        return redirect('fees:fees_setup')

@module_required('fees', 'edit')
@login_required
@require_POST
@csrf_protect
def delete_fees_type(request, pk):
    # Explicit auth check for security
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        from .models import FeesType
        fee_type = FeesType.objects.get(id=pk)
        fee_name = fee_type.fee_type
        fee_type.delete()
        messages.success(request, f"Perfect! Fee type '{fee_name}' has been deleted successfully.")
    except FeesType.DoesNotExist:
        messages.error(request, "Fee type not found.")
    except Exception as e:
        messages.error(request, "We couldn't delete the fee type right now. Please try again.")
    
    return redirect('fees:fees_setup')

@module_required('fees', 'edit')
@login_required
@require_POST
@csrf_protect
def bulk_delete_fees_type(request):
    # Explicit auth check for security
    if not request.user.is_authenticated:
        return redirect('login')
    try:
        # Validate selected items
        selected_ids = request.POST.getlist('selected_fees')
        if not selected_ids:
            messages.error(request, "Please select at least one fee type to delete.")
            return redirect('fees:fees_setup')
        
        # Validate each ID
        valid_ids = []
        for fee_id in selected_ids:
            try:
                id_int = int(fee_id)
                if id_int > 0:
                    valid_ids.append(id_int)
            except (ValueError, TypeError):
                continue
        
        if not valid_ids:
            messages.error(request, "No valid fee types selected for deletion.")
            return redirect('fees:fees_setup')
        
        # Log the bulk deletion attempt
        logger.info(f"User {request.user.id} attempting bulk delete of fee types: {valid_ids}")
        
        # Actual bulk deletion
        from .models import FeesType
        deleted_count = FeesType.objects.filter(id__in=valid_ids).delete()[0]
        messages.success(request, f"Perfect! {deleted_count} fee type(s) have been removed successfully.")
        
    except Exception as e:
        logger.error(f"Error in bulk_delete_fees_type by user {request.user.id}: {str(e)}")
        messages.error(request, "We couldn't delete the selected fee types right now. Please try again.")
    
    return redirect('fees:fees_setup')

@login_required
@csrf_protect
@module_required('fees', 'view')
def fees_carry_forward(request):
    try:
        from students.models import Student
        from subjects.models import ClassSection
        from django.core.paginator import Paginator
        
        if request.method == 'POST':
            # Handle saving due amounts
            for key, value in request.POST.items():
                if key.startswith('due_amount_'):
                    student_id = key.replace('due_amount_', '')
                    try:
                        student = Student.objects.get(id=student_id)
                        student.due_amount = float(value) if value else 0.00
                        student.save()
                    except (Student.DoesNotExist, ValueError):
                        continue
            
            messages.success(request, "Great! Due amounts have been updated successfully.")
            return redirect('fees:fees_carry_forward')
        
        # Get pagination parameters
        page_size = int(request.GET.get('page_size', 20))
        page = request.GET.get('page', 1)
        
        # Get all students for carry forward
        students_qs = Student.objects.select_related('class_section').all().order_by('first_name')
        classes = ClassSection.objects.all().order_by('class_name', 'section_name')
        
        # Filter by class if provided
        class_filter = request.GET.get('class_id')
        if class_filter and class_filter != 'None':
            students_qs = students_qs.filter(class_section_id=class_filter)
        
        # Pagination
        paginator = Paginator(students_qs, page_size)
        students = paginator.get_page(page)
        
        context = {
            'students': students,
            'classes': classes,
            'selected_class': class_filter,
            'page_size': page_size
        }
        
        return render(request, 'fees/fees_carry_forward.html', context)
    except Exception as e:
        logger.error(f"Error in fees_carry_forward for user {request.user.id}: {str(e)}")
        messages.error(request, "We're having trouble loading the carry forward page. Please try again.")
        return render(request, 'fees/fees_carry_forward.html', {'students': [], 'classes': []})

@login_required
@require_POST
@csrf_protect
def get_fee_group_context(request):
    """API endpoint to get context information for a fee group"""
    try:
        fee_group_id = request.POST.get('fee_group_id')
        if not fee_group_id:
            return JsonResponse({'error': 'Fee group ID required'}, status=400)
        
        from .models import FeesGroup
        fee_group = FeesGroup.objects.get(id=fee_group_id)
        
        context_info = {
            'group_type': fee_group.group_type,
            'fee_type': fee_group.fee_type,
            'fee_group_name': fee_group.fee_group,
            'requires_months': 'monthly' in fee_group.fee_group.lower(),
            'requires_classes': 'class based' in fee_group.fee_type.lower(),
            'requires_stoppages': 'stoppage based' in fee_group.fee_type.lower(),
            'requires_custom_name': 'general' in fee_group.fee_type.lower(),
        }
        
        return JsonResponse({'success': True, 'context': context_info})
        
    except FeesGroup.DoesNotExist:
        return JsonResponse({'error': 'Fee group not found'}, status=404)
    except Exception as e:
        logger.error(f"Error in get_fee_group_context: {str(e)}")
        return JsonResponse({'error': 'Server error'}, status=500)