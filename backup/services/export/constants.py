# backup/services/export/constants.py
"""Export constants and configuration"""

class ExportConstants:
    MAX_RECORDS_PDF = 1000
    MAX_RECORDS_CSV = 5000
    CACHE_TIMEOUT = 300  # 5 minutes
    PDF_CHUNK_SIZE = 100
    
    # Column widths for PDF tables
    STUDENT_COL_WIDTHS = [0.8, 1.8, 1.0, 1.0, 1.0, 1.2, 0.8]
    
    # CSV Headers mapping
    CSV_HEADERS = {
        'students': ['Admission Number', 'First Name', 'Last Name', 'Father Name', 'Mother Name', 
                    'Date of Birth', 'Date of Admission', 'Gender', 'Religion', 'Caste Category',
                    'Mobile Number', 'Email', 'Address', 'Class Section', 'Aadhaar Number', 
                    'PEN Number', 'Blood Group', 'Attendance %', 'Final Due'],
        'teachers': ['Teacher ID', 'Name', 'Mobile Number', 'Email', 'Qualification', 'Joining Date'],
        'subjects': ['Class Name', 'Section', 'Room Number', 'Student Count', 'Subject', 'Teacher', 'Assignment Status', 'Created Date'],
        'transport': ['Student Name', 'Admission No', 'Class', 'Route Name', 'Stoppage Name', 'Pickup Time', 'Assignment Date', 'Status', 'Mobile Number', 'Address'],
        'fees': ['Fee Group', 'Group Type', 'Fee Type', 'Amount Type', 'Month Name', 'Class Name', 'Stoppage Name', 'Amount', 'Student Count'],

        'student_fees': ['Receipt No', 'Student', 'Date', 'Payment Mode', 'Transaction No', 'Fee Breakdown', 'Total Amount', 'Total Discount', 'Final Paid', 'Payment Source'],
        'attendance': ['Student', 'Class Section', 'Date', 'Status', 'Created At'],
        'users': ['Username', 'Email', 'Role', 'Mobile Number', 'Is Active', 'Is Staff', 'Is Superuser', 'Date Joined', 'Last Login'],
        'fees_report': ['Student Name', 'Admission Number', 'Class Section', 'Total Fees', 
                       'Amount Paid', 'Discount', 'CF Due', 'Fine Paid', 'Fine Unpaid', 
                       'Final Due', 'Payment Status', 'Mobile Number', 'Email']
    }