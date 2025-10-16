"""
Transport Management Algorithms
Efficient algorithms for transport assignment and route optimization.
"""

from django.db.models import Count, Q
from django.core.exceptions import ValidationError
from .models import Route, Stoppage, TransportAssignment
from students.models import Student
import logging

logger = logging.getLogger(__name__)

class TransportAssignmentAlgorithm:
    """Algorithm for efficient transport assignment operations."""
    
    @staticmethod
    def validate_assignment(student_id, stoppage_id, exclude_assignment_id=None):
        """
        Validate if a student can be assigned to a stoppage.
        
        Args:
            student_id: ID of the student
            stoppage_id: ID of the stoppage
            exclude_assignment_id: ID of assignment to exclude (for editing)
            
        Returns:
            dict: {'valid': bool, 'message': str}
        """
        try:
            student = Student.objects.get(id=student_id)
            stoppage = Stoppage.objects.get(id=stoppage_id)
        except (Student.DoesNotExist, Stoppage.DoesNotExist):
            return {'valid': False, 'message': 'Invalid student or stoppage selected.'}
        
        # Check if student is already assigned
        existing_query = TransportAssignment.objects.filter(student=student)
        if exclude_assignment_id:
            existing_query = existing_query.exclude(id=exclude_assignment_id)
            
        if existing_query.exists():
            existing = existing_query.first()
            return {
                'valid': False, 
                'message': f'{student.get_full_display_name()} is already assigned to {existing.stoppage.name} on route {existing.route.name}.'
            }
        
        return {'valid': True, 'message': 'Assignment is valid.'}
    
    @staticmethod
    def bulk_assign_students(student_ids, stoppage_id):
        """
        Efficiently assign multiple students to a stoppage.
        
        Args:
            student_ids: List of student IDs
            stoppage_id: ID of the stoppage
            
        Returns:
            dict: {'success_count': int, 'error_count': int, 'errors': list}
        """
        try:
            stoppage = Stoppage.objects.get(id=stoppage_id)
        except Stoppage.DoesNotExist:
            return {'success_count': 0, 'error_count': len(student_ids), 'errors': ['Invalid stoppage selected.']}
        
        success_count = 0
        error_count = 0
        errors = []
        
        # Get already assigned students to avoid duplicates
        already_assigned = set(
            TransportAssignment.objects.filter(
                student_id__in=student_ids
            ).values_list('student_id', flat=True)
        )
        
        # Get valid students
        valid_students = Student.objects.filter(
            id__in=student_ids
        ).exclude(id__in=already_assigned)
        
        # Bulk create assignments
        assignments_to_create = []
        for student in valid_students:
            assignments_to_create.append(
                TransportAssignment(
                    student=student,
                    route=stoppage.route,
                    stoppage=stoppage
                )
            )
        
        if assignments_to_create:
            TransportAssignment.objects.bulk_create(assignments_to_create)
            success_count = len(assignments_to_create)
        
        # Count errors
        error_count = len(student_ids) - success_count
        
        return {
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors
        }
    
    @staticmethod
    def get_unassigned_students():
        """Get students who don't have transport assignments."""
        assigned_student_ids = TransportAssignment.objects.values_list('student_id', flat=True)
        return Student.objects.exclude(id__in=assigned_student_ids).order_by('first_name', 'last_name')
    
    @staticmethod
    def get_route_statistics():
        """Get statistics for all routes."""
        return Route.objects.annotate(
            stoppage_count=Count('stoppage'),
            assignment_count=Count('stoppage__transportassignment')
        ).order_by('name')
    
    @staticmethod
    def get_stoppage_statistics():
        """Get statistics for all stoppages."""
        return Stoppage.objects.select_related('route').annotate(
            assignment_count=Count('transportassignment')
        ).order_by('route__name', 'name')

class RouteOptimizationAlgorithm:
    """Algorithm for route optimization and management."""
    
    @staticmethod
    def validate_route_deletion(route_id):
        """
        Check if a route can be safely deleted.
        
        Args:
            route_id: ID of the route to delete
            
        Returns:
            dict: {'can_delete': bool, 'message': str, 'stoppage_count': int}
        """
        try:
            route = Route.objects.get(id=route_id)
        except Route.DoesNotExist:
            return {'can_delete': False, 'message': 'Route not found.', 'stoppage_count': 0}
        
        stoppage_count = route.stoppage_set.count()
        
        if stoppage_count > 0:
            return {
                'can_delete': False,
                'message': f'Cannot delete route "{route.name}" because it has {stoppage_count} stoppages. Please remove the stoppages first.',
                'stoppage_count': stoppage_count
            }
        
        return {
            'can_delete': True,
            'message': f'Route "{route.name}" can be safely deleted.',
            'stoppage_count': 0
        }
    
    @staticmethod
    def validate_stoppage_deletion(stoppage_id):
        """
        Check if a stoppage can be safely deleted.
        
        Args:
            stoppage_id: ID of the stoppage to delete
            
        Returns:
            dict: {'can_delete': bool, 'message': str, 'assignment_count': int}
        """
        try:
            stoppage = Stoppage.objects.get(id=stoppage_id)
        except Stoppage.DoesNotExist:
            return {'can_delete': False, 'message': 'Stoppage not found.', 'assignment_count': 0}
        
        assignment_count = stoppage.transportassignment_set.count()
        
        if assignment_count > 0:
            return {
                'can_delete': False,
                'message': f'Cannot delete stoppage "{stoppage.name}" because {assignment_count} students are assigned to it. Please reassign the students first.',
                'assignment_count': assignment_count
            }
        
        return {
            'can_delete': True,
            'message': f'Stoppage "{stoppage.name}" can be safely deleted.',
            'assignment_count': 0
        }

class TransportSearchAlgorithm:
    """Algorithm for searching and filtering transport data."""
    
    @staticmethod
    def search_students_for_assignment(query, limit=10):
        """
        Search for students available for transport assignment.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            
        Returns:
            QuerySet: Filtered students
        """
        # Get unassigned students
        unassigned_students = TransportAssignmentAlgorithm.get_unassigned_students()
        
        if query:
            unassigned_students = unassigned_students.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(admission_number__icontains=query)
            )
        
        return unassigned_students[:limit]
    
    @staticmethod
    def search_routes(query):
        """Search routes by name."""
        routes = Route.objects.all()
        
        if query:
            routes = routes.filter(name__icontains=query)
        
        return routes.order_by('name')
    
    @staticmethod
    def search_stoppages(query, route_id=None):
        """Search stoppages by name and optionally filter by route."""
        stoppages = Stoppage.objects.select_related('route')
        
        if query:
            stoppages = stoppages.filter(name__icontains=query)
        
        if route_id:
            stoppages = stoppages.filter(route_id=route_id)
        
        return stoppages.order_by('route__name', 'name')
    
    @staticmethod
    def search_assignments(query):
        """Search transport assignments."""
        assignments = TransportAssignment.objects.select_related(
            'student', 'route', 'stoppage'
        )
        
        if query:
            assignments = assignments.filter(
                Q(student__first_name__icontains=query) |
                Q(student__last_name__icontains=query) |
                Q(student__admission_number__icontains=query) |
                Q(route__name__icontains=query) |
                Q(stoppage__name__icontains=query)
            )
        
        return assignments.order_by('-assigned_date')