# student_fees/export_views.py
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from users.decorators import module_required
from backup.services.export_service import DataExportService

@login_required
@module_required('payments', 'view')
def export_final_due_report(request, format_type):
    """Export final due report in specified format"""
    try:
        if format_type == 'csv':
            return DataExportService.export_to_csv('fees_report', request.user)
        elif format_type == 'excel':
            return DataExportService.export_to_excel('fees_report', request.user)
        elif format_type == 'pdf':
            return DataExportService.export_to_pdf('fees_report', request.user)
        else:
            return HttpResponse('Format not supported', status=400)
    except Exception as e:
        return HttpResponse(f'Export failed: {str(e)}', status=500)