# 🔒 EXPORT CODE PROTECTION WARNING
"""
⚠️  CRITICAL WARNING ⚠️

STUDENTS AND TEACHERS EXPORT CODE IS LOCKED
DO NOT MODIFY THE FOLLOWING FUNCTIONS:

LOCKED FUNCTIONS (NO CHANGES ALLOWED):
- format_student_row()
- format_teacher_row() 
- _organize_students_by_class_and_name()
- Students module query logic
- Teachers module query logic

These functions are PRODUCTION READY and working correctly.
Any modifications may break existing functionality.

UNLOCKED FUNCTIONS (Improvements Allowed):
- format_subject_row()
- format_transport_row()
- format_fees_row()
- format_student_fees_row()
- format_fines_row()
- format_attendance_row()
- format_promotion_row()
- format_messaging_row()
- format_users_row()
- format_fees_report_row() - CRITICAL PRIORITY
- _get_fee_report_data() - CRITICAL PRIORITY

NEXT PRIORITY: Fix fees_report HTTP 500 errors
"""

# Protection flags
STUDENTS_EXPORT_LOCKED = True
TEACHERS_EXPORT_LOCKED = True

# Locked module list
LOCKED_MODULES = ['students', 'teachers']
UNLOCKED_MODULES = [
    'subjects', 'transport', 'fees', 'student_fees', 
    'fines', 'attendance', 'promotion', 'messaging', 
    'users', 'fees_report'
]

def check_module_lock_status(module_name):
    """Check if module export code is locked"""
    if module_name in LOCKED_MODULES:
        return f"🔒 {module_name.upper()} EXPORT IS LOCKED - NO MODIFICATIONS ALLOWED"
    else:
        return f"🔧 {module_name.upper()} EXPORT IS UNLOCKED - IMPROVEMENTS ALLOWED"

# Usage example:
# print(check_module_lock_status('students'))  # 🔒 STUDENTS EXPORT IS LOCKED
# print(check_module_lock_status('fees_report'))  # 🔧 FEES_REPORT EXPORT IS UNLOCKED