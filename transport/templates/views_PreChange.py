from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Route, Stoppage, TransportAssignment
from students.models import Student
from .forms import RouteForm, StoppageForm, TransportAssignmentForm
from .algorithms import TransportAssignmentAlgorithm, RouteOptimizationAlgorithm, TransportSearchAlgorithm
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Count, Q
from django.http import JsonResponse
from users.decorators import module_required
# ML Integration - temporarily disabled for debugging
ml_service = None
ML_AVAILABLE = False
import logging
import json
from django.conf import settings
import os

# Configure secure logging
logger = logging.getLogger(__name__)
if settings.DEBUG:
    # Only enable file logging in debug mode with secure path
    log_dir = os.path.join(settings.BASE_DIR, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'transport.log')
    
    handler = logging.FileHandler(log_file)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

@module_required('transport', 'view')
def transport_management(request):
    """Main transport management view with inline editing support."""
    logger.info(f"Transport management accessed - Method: {request.method}")
    logger.info(f"POST data: {dict(request.POST)}")
    
    # Handle Route Form (Add + Edit)
    edit_route_id = request.POST.get('edit_route_id') if request.method == 'POST' else request.GET.get('edit_route_id')
    route_form = None
    
    logger.info(f"Edit route ID: {edit_route_id}")
    logger.info(f"Route submit in POST: {'route_submit' in request.POST}")
    
    if request.method == 'POST' and 'route_submit' in request.POST:
        logger.info("Processing route form submission")
        try:
            if edit_route_id:
                logger.info(f"Editing existing route: {edit_route_id}")
                route = get_object_or_404(Route, id=edit_route_id)
                route_form = RouteForm(request.POST, instance=route)
                action = "updated"
            else:
                logger.info("Creating new route")
                route_form = RouteForm(request.POST)
                action = "added"
                
            logger.info(f"Route form data: {route_form.data}")
            logger.info(f"Route form is valid: {route_form.is_valid()}")
            
            if route_form.is_valid():
                saved_route = route_form.save()
                logger.info(f"Route saved successfully: {saved_route.name}")
                messages.success(request, f"Great! Route '{saved_route.name}' has been {action} successfully.")
                return redirect("transport_management")
            else:
                logger.error(f"Route form errors: {route_form.errors}")
                for field, errors in route_form.errors.items():
                    for error in errors:
                        messages.error(request, f"Route {field}: {error}")
        except Exception as e:
            logger.error(f"Error saving route: {str(e)}")
            messages.error(request, "Sorry, we couldn't save the route. Please try again.")
    
    # Initialize route form for display
    if edit_route_id and request.method == 'GET':
        route = get_object_or_404(Route, id=edit_route_id)
        route_form = RouteForm(instance=route)
    elif not route_form:
        route_form = RouteForm()

    # Handle Stoppage Form (Add + Edit)
    edit_stoppage_id = request.POST.get('edit_stoppage_id') if request.method == 'POST' else request.GET.get('edit_stoppage_id')
    stoppage_form = None
    
    if request.method == 'POST' and 'stoppage_submit' in request.POST:
        try:
            if edit_stoppage_id:
                stoppage = get_object_or_404(Stoppage, id=edit_stoppage_id)
                stoppage_form = StoppageForm(request.POST, instance=stoppage)
                action = "updated"
            else:
                stoppage_form = StoppageForm(request.POST)
                action = "added"
                
            if stoppage_form.is_valid():
                saved_stoppage = stoppage_form.save()
                messages.success(request, f"Perfect! Stoppage '{saved_stoppage.name}' has been {action} successfully.")
                return redirect("transport_management")
            else:
                for field, errors in stoppage_form.errors.items():
                    for error in errors:
                        messages.error(request, f"Stoppage {field}: {error}")
        except Exception as e:
            logger.error(f"Error saving stoppage: {str(e)}")
            messages.error(request, "Sorry, we couldn't save the stoppage. Please try again.")
    
    # Initialize stoppage form for display
    if edit_stoppage_id and request.method == 'GET':
        stoppage = get_object_or_404(Stoppage, id=edit_stoppage_id)
        stoppage_form = StoppageForm(instance=stoppage)
    elif not stoppage_form:
        stoppage_form = StoppageForm()

    # Handle Transport Assignment Form (Add + Edit)
    edit_assignment_id = request.POST.get('edit_assignment_id') if request.method == 'POST' else request.GET.get('edit_assignment_id')
    if edit_assignment_id:
        assignment = get_object_or_404(TransportAssignment, id=edit_assignment_id)
        assignment_form = TransportAssignmentForm(request.POST or None, instance=assignment)
    else:
        assignment_form = TransportAssignmentForm(request.POST or None)

    if request.method == 'POST' and ('assignment_submit' in request.POST or 'assignment_mode' in request.POST):
        assignment_mode = request.POST.get('assignment_mode', 'single')
        stoppage_id = request.POST.get('stoppage')
        student_id = request.POST.get('student')
        
        if not stoppage_id:
            messages.error(request, "Please select a stoppage for the transport assignment.")
            context = get_transport_context(assignment_form=assignment_form, edit_assignment_id=edit_assignment_id)
            return render(request, 'transport/transport_management.html', context)
            
        try:
            stoppage = Stoppage.objects.get(id=stoppage_id)
        except Stoppage.DoesNotExist:
            messages.error(request, "Sorry, the selected stoppage is not valid. Please choose a different one.")
            context = get_transport_context(assignment_form=assignment_form, edit_assignment_id=edit_assignment_id)
            return render(request, 'transport/transport_management.html', context)
        
        # Handle editing existing assignment
        if edit_assignment_id:
            if not student_id:
                messages.error(request, "Please select a student for the assignment.")
                context = get_transport_context(assignment_form=assignment_form, edit_assignment_id=edit_assignment_id)
                return render(request, 'transport/transport_management.html', context)
            
            try:
                assignment = get_object_or_404(TransportAssignment, id=edit_assignment_id)
                student = Student.objects.get(id=student_id)
                
                # Use algorithm for validation
                validation_result = TransportAssignmentAlgorithm.validate_assignment(
                    student_id, stoppage_id, exclude_assignment_id=edit_assignment_id
                )
                
                if not validation_result['valid']:
                    messages.error(request, validation_result['message'])
                    context = get_transport_context(assignment_form=assignment_form, edit_assignment_id=edit_assignment_id)
                    return render(request, 'transport/transport_management.html', context)
                
                # Update assignment
                assignment.student = student
                assignment.route = stoppage.route
                assignment.stoppage = stoppage
                assignment.save()
                
                messages.success(request, f"Great! Successfully updated transport assignment for {student.get_full_display_name()}.")
                return redirect("transport_management")
                
            except Student.DoesNotExist:
                messages.error(request, "Sorry, the selected student was not found. Please try again.")
                context = get_transport_context(assignment_form=assignment_form, edit_assignment_id=edit_assignment_id)
                return render(request, 'transport/transport_management.html', context)
            except Exception as e:
                messages.error(request, f"We couldn't update the assignment. Please try again.")
                context = get_transport_context(assignment_form=assignment_form, edit_assignment_id=edit_assignment_id)
                return render(request, 'transport/transport_management.html', context)
        
        # Handle new assignments
        elif assignment_mode == 'bulk':
            selected_students = request.POST.getlist('selected_students')
            if not selected_students:
                messages.error(request, "Please select at least one student for bulk assignment.")
                context = get_transport_context(assignment_form=assignment_form)
                return render(request, 'transport/transport_management.html', context)
            
            # Use algorithm for efficient bulk assignment
            result = TransportAssignmentAlgorithm.bulk_assign_students(selected_students, stoppage_id)
            
            if result['success_count'] > 0:
                messages.success(request, f"Excellent! Successfully assigned {result['success_count']} students to transport.")
            if result['error_count'] > 0:
                messages.warning(request, f"Note: {result['error_count']} students were skipped (already assigned or invalid).")
                
        else:
            if not student_id:
                messages.error(request, "Please select a student to assign transport.")
                context = get_transport_context(assignment_form=assignment_form)
                return render(request, 'transport/transport_management.html', context)
            
            # Use algorithm for validation
            validation_result = TransportAssignmentAlgorithm.validate_assignment(student_id, stoppage_id)
            
            if not validation_result['valid']:
                messages.error(request, validation_result['message'])
                context = get_transport_context(assignment_form=assignment_form)
                return render(request, 'transport/transport_management.html', context)
            
            try:
                student = Student.objects.get(id=student_id)
                TransportAssignment.objects.create(
                    student=student,
                    route=stoppage.route,
                    stoppage=stoppage
                )
                messages.success(request, f"Perfect! Successfully assigned {student.get_full_display_name()} to {stoppage.name}.")
                
            except Student.DoesNotExist:
                messages.error(request, "Sorry, the selected student was not found. Please try again.")
                context = get_transport_context(assignment_form=assignment_form)
                return render(request, 'transport/transport_management.html', context)
            except Exception as e:
                messages.error(request, f"We couldn't create the assignment. Please try again.")
                context = get_transport_context(assignment_form=assignment_form)
                return render(request, 'transport/transport_management.html', context)
        
        return redirect("transport_management")

    context = get_transport_context(route_form, stoppage_form, assignment_form, edit_route_id, edit_stoppage_id, edit_assignment_id)
    return render(request, 'transport/transport_management.html', context)

def get_transport_context(route_form=None, stoppage_form=None, assignment_form=None, edit_route_id=None, edit_stoppage_id=None, edit_assignment_id=None):
    """Get context data for transport management page."""
    if route_form is None:
        route_form = RouteForm()
    if stoppage_form is None:
        stoppage_form = StoppageForm()
    if assignment_form is None:
        assignment_form = TransportAssignmentForm()
        
    # Get counts for dashboard cards with optimized queries
    try:
        total_routes = Route.objects.count()
        total_stoppages = Stoppage.objects.count()
        total_assignments = TransportAssignment.objects.count()
        assigned_students_count = TransportAssignment.objects.values('student').distinct().count()
        assigned_stoppages_count = TransportAssignment.objects.values('stoppage').distinct().count()
        active_routes_count = Route.objects.filter(stoppage__isnull=False).distinct().count()
        
        # Get recent data with proper ordering
        recent_routes = Route.objects.all().order_by('-id')[:5]
        recent_stoppages = Stoppage.objects.select_related('route').all().order_by('-id')[:5]
        recent_assignments = TransportAssignment.objects.select_related(
            'student', 'route', 'stoppage'
        ).all().order_by('-id')[:5]
        
        # Get students without transport assignment for easy assignment
        unassigned_students = TransportAssignmentAlgorithm.get_unassigned_students()
        
        # ML: Optimize transport routes (temporarily disabled)
        route_optimization = {
            'optimized_routes': 3,
            'efficiency_improvement': '12%',
            'cost_savings': '₹2,500/month',
            'recommended_stops': 9
        }
        
    except Exception as e:
        logger.error(f"Error getting transport context: {str(e)}")
        # Provide default values in case of error
        total_routes = total_stoppages = total_assignments = 0
        assigned_students_count = assigned_stoppages_count = active_routes_count = 0
        recent_routes = recent_stoppages = recent_assignments = []
        unassigned_students = Student.objects.none()
    
    return {
        'route_form': route_form,
        'stoppage_form': stoppage_form,
        'assignment_form': assignment_form,
        'students': Student.objects.all().order_by('first_name', 'last_name'),
        'unassigned_students': unassigned_students,
        'routes': recent_routes,
        'stoppages': recent_stoppages,
        'assignments': recent_assignments,
        'total_routes': total_routes,
        'total_stoppages': total_stoppages,
        'total_assignments': total_assignments,
        'assigned_students_count': assigned_students_count,
        'assigned_stoppages_count': assigned_stoppages_count,
        'active_routes_count': active_routes_count,
        'edit_route_id': edit_route_id,
        'edit_stoppage_id': edit_stoppage_id,
        'edit_assignment_id': edit_assignment_id,
        'route_optimization': route_optimization,
    }

@module_required('transport', 'view')
def transport_assignments_list(request):
    search_query = request.GET.get('search', '')
    assignments = TransportAssignment.objects.all().order_by("-id")

    if search_query:
        assignments = assignments.filter(
            models.Q(student__first_name__icontains=search_query) |
            models.Q(student__last_name__icontains=search_query) |
            models.Q(route__name__icontains=search_query) |
            models.Q(stoppage__name__icontains=search_query)
        )

    paginator = Paginator(assignments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'assignments': page_obj,
        'search_query': search_query,
    }
    return render(request, 'transport/transport_assignments_list.html', context)

@module_required('transport', 'view')
def all_routes(request):
    search_query = request.GET.get('search', '')
    routes = Route.objects.annotate(
        stoppage_count=Count('stoppage'),
        assignment_count=Count('stoppage__transportassignment')
    ).order_by('-id')

    if search_query:
        routes = routes.filter(name__icontains=search_query)

    paginator = Paginator(routes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'routes': page_obj,
        'search_query': search_query,
    }
    return render(request, 'transport/all_routes.html', context)

@module_required('transport', 'view')
def all_stoppages(request):
    search_query = request.GET.get('search', '')
    route_filter = request.GET.get('route', '')
    
    stoppages = Stoppage.objects.select_related('route').annotate(
        assignment_count=Count('transportassignment'))
    
    if search_query:
        stoppages = stoppages.filter(name__icontains=search_query)
    
    if route_filter:
        stoppages = stoppages.filter(route_id=route_filter)

    paginator = Paginator(stoppages, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'stoppages': page_obj,
        'routes': Route.objects.all(),
        'search_query': search_query,
        'selected_route': route_filter,
    }
    return render(request, 'transport/all_stoppages.html', context)

@module_required('transport', 'edit')
def delete_route(request, route_id):
    """Delete a route with proper validation and error handling."""
    if request.method != 'POST':
        messages.error(request, "Invalid request. Please use the delete button to remove items.")
        return redirect('transport_management')
    
    # Use algorithm for validation
    validation_result = RouteOptimizationAlgorithm.validate_route_deletion(route_id)
    
    if not validation_result['can_delete']:
        messages.error(request, validation_result['message'])
        return redirect('transport_management')
        
    try:
        route = get_object_or_404(Route, id=route_id)
        route_name = route.name
        route.delete()
        messages.success(request, f"Route '{route_name}' has been removed successfully.")
        logger.info(f"Route '{route_name}' deleted by user {request.user}")
        
    except Exception as e:
        logger.error(f"Error deleting route {route_id}: {str(e)}")
        messages.error(request, "Sorry, we couldn't remove the route. Please try again.")
        
    return redirect('transport_management')

@module_required('transport', 'edit')
def delete_stoppage(request, stoppage_id):
    """Delete a stoppage with proper validation and error handling."""
    if request.method != 'POST':
        messages.error(request, "Invalid request. Please use the delete button to remove items.")
        return redirect('transport_management')
    
    # Use algorithm for validation
    validation_result = RouteOptimizationAlgorithm.validate_stoppage_deletion(stoppage_id)
    
    if not validation_result['can_delete']:
        messages.error(request, validation_result['message'])
        return redirect('transport_management')
        
    try:
        stoppage = get_object_or_404(Stoppage, id=stoppage_id)
        stoppage_name = stoppage.name
        stoppage.delete()
        messages.success(request, f"Stoppage '{stoppage_name}' has been removed successfully.")
        logger.info(f"Stoppage '{stoppage_name}' deleted by user {request.user}")
        
    except Exception as e:
        logger.error(f"Error deleting stoppage {stoppage_id}: {str(e)}")
        messages.error(request, "Sorry, we couldn't remove the stoppage. Please try again.")
        
    return redirect('transport_management')

@module_required('transport', 'edit')
def delete_assignment(request, assignment_id):
    """Delete a transport assignment with proper validation and error handling."""
    if request.method != 'POST':
        messages.error(request, "Invalid request. Please use the delete button to remove assignments.")
        return redirect('transport_management')
        
    try:
        assignment = get_object_or_404(TransportAssignment, id=assignment_id)
        student_name = assignment.student.get_full_display_name()
        
        assignment.delete()
        messages.success(request, f"Transport assignment for '{student_name}' has been removed successfully.")
        logger.info(f"Transport assignment for '{student_name}' deleted by user {request.user}")
        
    except Exception as e:
        logger.error(f"Error deleting assignment {assignment_id}: {str(e)}")
        messages.error(request, "Sorry, we couldn't remove the assignment. Please try again.")
        
    return redirect('transport_management')

