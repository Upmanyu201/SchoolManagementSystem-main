"""
Debug script to check transport assignments
"""

def debug_transport_assignments():
    from students.models import Student
    from transport.models import TransportAssignment
    
    print("=== Transport Assignment Debug ===")
    
    # Check all students
    students = Student.objects.all()
    print(f"Total students: {students.count()}")
    
    # Check all transport assignments
    assignments = TransportAssignment.objects.all()
    print(f"Total transport assignments: {assignments.count()}")
    
    # Check specific student
    try:
        student = Student.objects.get(admission_number='GVIS01005')
        print(f"Found student: {student.name} (ID: {student.id})")
        
        # Check if this student has transport assignment
        assignment = TransportAssignment.objects.filter(student=student).first()
        if assignment:
            print(f"Transport assignment found: {assignment.route.name} - {assignment.stoppage.name}")
        else:
            print("No transport assignment found for this student")
            
        # Check all assignments for debugging
        all_assignments = TransportAssignment.objects.select_related('student', 'route', 'stoppage').all()
        print("\nAll transport assignments:")
        for assign in all_assignments:
            print(f"- Student: {assign.student.admission_number} ({assign.student.name}) -> {assign.route.name} - {assign.stoppage.name}")
            
    except Student.DoesNotExist:
        print("Student GVIS01005 not found")
    
    return True

if __name__ == "__main__":
    debug_transport_assignments()