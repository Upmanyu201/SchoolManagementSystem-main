"""
Transport API Views
RESTful API endpoints for transport management operations.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
from .algorithms import TransportSearchAlgorithm, TransportAssignmentAlgorithm
from .models import Route, Stoppage, TransportAssignment
from students.models import Student

@login_required
@require_http_methods(["GET"])
def search_students_api(request):
    """
    API endpoint to search for students available for transport assignment.
    """
    query = request.GET.get('q', '').strip()
    limit = int(request.GET.get('limit', 10))
    
    try:
        students = TransportSearchAlgorithm.search_students_for_assignment(query, limit)
        
        results = []
        for student in students:
            results.append({
                'id': student.id,
                'name': student.get_full_display_name(),
                'admission_number': student.admission_number,
                'class_name': student.student_class.name if student.student_class else 'N/A',
                'avatar_initials': f"{student.first_name[0]}{student.last_name[0]}" if student.first_name and student.last_name else 'NA'
            })
        
        return JsonResponse({
            'success': True,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["GET"])
def get_route_stoppages_api(request, route_id):
    """
    API endpoint to get stoppages for a specific route.
    """
    try:
        route = Route.objects.get(id=route_id)
        stoppages = route.stoppage_set.all().order_by('name')
        
        results = []
        for stoppage in stoppages:
            results.append({
                'id': stoppage.id,
                'name': stoppage.name,
                'assignment_count': stoppage.transportassignment_set.count()
            })
        
        return JsonResponse({
            'success': True,
            'route_name': route.name,
            'stoppages': results
        })
        
    except Route.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Route not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["POST"])
def validate_assignment_api(request):
    """
    API endpoint to validate transport assignment before submission.
    """
    try:
        data = json.loads(request.body)
        student_id = data.get('student_id')
        stoppage_id = data.get('stoppage_id')
        exclude_assignment_id = data.get('exclude_assignment_id')
        
        if not student_id or not stoppage_id:
            return JsonResponse({
                'success': False,
                'error': 'Student ID and Stoppage ID are required'
            }, status=400)
        
        result = TransportAssignmentAlgorithm.validate_assignment(
            student_id, stoppage_id, exclude_assignment_id
        )
        
        return JsonResponse({
            'success': True,
            'valid': result['valid'],
            'message': result['message']
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@method_decorator(login_required, name='dispatch')
class TransportStatsAPI(View):
    """
    API endpoint for transport statistics.
    """
    
    def get(self, request):
        """Get transport statistics."""
        try:
            # Get basic counts
            total_routes = Route.objects.count()
            total_stoppages = Stoppage.objects.count()
            total_assignments = TransportAssignment.objects.count()
            
            # Get unassigned students count
            unassigned_count = TransportAssignmentAlgorithm.get_unassigned_students().count()
            
            # Get route statistics
            route_stats = TransportAssignmentAlgorithm.get_route_statistics()
            
            routes_data = []
            for route in route_stats:
                routes_data.append({
                    'id': route.id,
                    'name': route.name,
                    'stoppage_count': route.stoppage_count,
                    'assignment_count': route.assignment_count
                })
            
            return JsonResponse({
                'success': True,
                'stats': {
                    'total_routes': total_routes,
                    'total_stoppages': total_stoppages,
                    'total_assignments': total_assignments,
                    'unassigned_students': unassigned_count,
                    'routes': routes_data
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

@login_required
@require_http_methods(["GET"])
def suggest_routes_by_address(request):
    """
    API endpoint to suggest optimal routes based on student addresses.
    """
    try:
        address_query = request.GET.get('address', '').strip().lower()
        
        if not address_query:
            return JsonResponse({
                'success': False,
                'error': 'Address query is required'
            }, status=400)
        
        # Find students with similar addresses
        students_in_area = Student.objects.filter(
            address__icontains=address_query
        ).select_related('class_section')
        
        # Get existing assignments for these students
        assigned_students = TransportAssignment.objects.filter(
            student__in=students_in_area
        ).select_related('route', 'stoppage', 'student')
        
        # Analyze route patterns
        route_suggestions = {}
        for assignment in assigned_students:
            route_name = assignment.route.name
            if route_name not in route_suggestions:
                route_suggestions[route_name] = {
                    'route_id': assignment.route.id,
                    'route_name': route_name,
                    'student_count': 0,
                    'stoppages': set(),
                    'students': []
                }
            
            route_suggestions[route_name]['student_count'] += 1
            route_suggestions[route_name]['stoppages'].add(assignment.stoppage.name)
            route_suggestions[route_name]['students'].append({
                'name': assignment.student.get_full_display_name(),
                'address': assignment.student.address
            })
        
        # Convert to list and sort by student count
        suggestions = []
        for route_data in route_suggestions.values():
            route_data['stoppages'] = list(route_data['stoppages'])
            suggestions.append(route_data)
        
        suggestions.sort(key=lambda x: x['student_count'], reverse=True)
        
        return JsonResponse({
            'success': True,
            'address_query': address_query,
            'total_students_in_area': students_in_area.count(),
            'assigned_students_in_area': assigned_students.count(),
            'route_suggestions': suggestions[:5],  # Top 5 suggestions
            'message': f'Found {len(suggestions)} route patterns for "{address_query}" area'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)