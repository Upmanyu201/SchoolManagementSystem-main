# reports/utils.py
# Export functionality removed - all export utilities have been removed

def get_class_order():
    """Define class ordering for reports"""
    return [
        'Play', 'Nursery', 'LKG', 'UKG',
        'Class_1', 'Class_2', 'Class_3', 'Class_4', 'Class_5',
        'Class_6', 'Class_7', 'Class_8', 'Class_9', 'Class_10',
        'Class_11', 'Class_12'
    ]

def sort_students_by_class(deposits):
    """Sort students by class order and section"""
    class_order = get_class_order()
    
    def get_sort_key(deposit):
        student = deposit.student
        class_name = student.student_class.name if student.student_class else 'ZZZ'
        section_name = student.student_section.name if student.student_section else 'ZZZ'
        
        try:
            class_index = class_order.index(class_name)
        except ValueError:
            class_index = 999
        
        return (class_index, section_name, student.first_name, student.last_name)
    
    return sorted(deposits, key=get_sort_key)
