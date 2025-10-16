# backup/services/export_service_legacy.py
# Legacy export service - DEPRECATED: Use modular export package instead
# This file is kept for backward compatibility only

# Import the new modular services
from .export import (
    DataExportService,
    CSVExporter,
    PDFExporter, 
    ExcelExporter,
    ExportConstants
)

# Legacy compatibility - redirect to new modular services
class LegacyDataExportService(DataExportService):
    """Legacy wrapper for backward compatibility"""
    
    @classmethod
    def export_to_csv(cls, module_name, user):
        return CSVExporter.export_to_csv(module_name, user)
    
    @classmethod
    def export_to_pdf(cls, module_name, user):
        return PDFExporter.export_to_pdf(module_name, user)
    
    @classmethod
    def export_to_excel(cls, module_name, user):
        return ExcelExporter.export_to_excel(module_name, user)

# Legacy compatibility - use new modular service
ExportService = LegacyDataExportService
DataExportService = LegacyDataExportService