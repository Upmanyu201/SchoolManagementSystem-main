from django.http import JsonResponse
from .exports import ExportService
from datetime import datetime

class ExportMixin:
    """Mixin to add export functionality to any view"""
    
    def get_export_data(self):
        """Override this method in your view to provide export data"""
        raise NotImplementedError("Subclasses must implement get_export_data()")
    
    def get_export_filename(self):
        """Override this method to provide custom filename"""
        return f"{self.__class__.__name__.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def handle_export(self, request, queryset=None):
        """Handle export requests"""
        export_format = request.GET.get('export')
        
        if not export_format:
            return None
        
        try:
            # Get data and filename
            if queryset is not None:
                data, headers = self.get_export_data(queryset)
            else:
                data, headers = self.get_export_data()
            
            filename = self.get_export_filename()
            
            # Export based on format
            if export_format == 'excel':
                return ExportService.export_to_xlsx(data, filename, headers)
            elif export_format == 'csv':
                return ExportService.export_to_csv(data, filename, headers)
            elif export_format == 'pdf':
                title = f"{self.__class__.__name__.replace('View', '').replace('List', '')} Report"
                return ExportService.export_to_pdf(data, filename, headers, title)
            else:
                return JsonResponse({'error': 'Invalid export format'}, status=400)
                
        except Exception as e:
            return JsonResponse({'error': f'Export failed: {str(e)}'}, status=500)