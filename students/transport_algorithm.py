"""
Transport Information Algorithm for Student Dashboard
"""

from transport.models import TransportAssignment
from django.core.exceptions import ObjectDoesNotExist


class TransportInfoAlgorithm:
    """Algorithm to fetch and format transport information for students."""
    
    @staticmethod
    def get_student_transport_info(student):
        """Get transport information for a specific student."""
        try:
            # Try multiple lookup methods
            assignment = None
            
            # Method 1: Direct student object lookup
            assignment = TransportAssignment.objects.select_related(
                'route', 'stoppage'
            ).filter(student=student).first()
            
            # Method 2: If not found, try by admission number variations
            if not assignment:
                # Try exact match
                assignment = TransportAssignment.objects.select_related(
                    'route', 'stoppage', 'student'
                ).filter(student__admission_number=student.admission_number).first()
                
                # Try case-insensitive
                if not assignment:
                    assignment = TransportAssignment.objects.select_related(
                        'route', 'stoppage', 'student'
                    ).filter(student__admission_number__iexact=student.admission_number).first()
                
                # Try partial match on admission number
                if not assignment:
                    # Get the numeric part (last 4-5 digits)
                    import re
                    numbers = re.findall(r'\d+', student.admission_number)
                    if numbers:
                        last_number = numbers[-1]
                        assignment = TransportAssignment.objects.select_related(
                            'route', 'stoppage', 'student'
                        ).filter(student__admission_number__icontains=last_number).first()
            
            if assignment:
                return {
                    'has_transport': True,
                    'route_name': assignment.route.name,
                    'stoppage_name': assignment.stoppage.name,
                    'assigned_date': assignment.assigned_date,
                    'display_text': f"{assignment.route.name} - {assignment.stoppage.name}"
                }
            else:
                return {
                    'has_transport': False,
                    'route_name': None,
                    'stoppage_name': None,
                    'assigned_date': None,
                    'display_text': 'No transport assigned'
                }
            
        except Exception as e:
            return {
                'has_transport': False,
                'route_name': None,
                'stoppage_name': None,
                'assigned_date': None,
                'display_text': 'No transport assigned'
            }
    
    @staticmethod
    def format_transport_display(transport_info):
        """Format transport information for display."""
        if not transport_info['has_transport']:
            return {
                'status': 'not_assigned',
                'icon': 'fas fa-times-circle',
                'color': 'text-gray-500',
                'title': 'No Transport',
                'subtitle': 'Transport not assigned'
            }
        
        return {
            'status': 'assigned',
            'icon': 'fas fa-bus',
            'color': 'text-green-600',
            'title': transport_info['route_name'],
            'subtitle': f"Stoppage: {transport_info['stoppage_name']}",
            'assigned_date': transport_info['assigned_date'].strftime('%d %b %Y') if transport_info['assigned_date'] else 'N/A'
        }