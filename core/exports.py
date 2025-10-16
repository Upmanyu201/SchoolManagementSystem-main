try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    pd = None
    PANDAS_AVAILABLE = False
from django.http import HttpResponse
from django.template.loader import render_to_string
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import csv
import logging
import time
from datetime import datetime

# Export-specific logger
export_logger = logging.getLogger('export.api')

class ExportService:
    """Universal Export Service for all School Management System modules"""
    
    @staticmethod
    def export_to_xlsx(data, filename, headers=None):
        """Export data to Excel (.xlsx) format"""
        if not PANDAS_AVAILABLE:
            # Fallback to CSV if pandas not available
            return ExportService.export_to_csv(data, filename, headers)
        
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
        
        # Create DataFrame
        df = pd.DataFrame(data)
        if headers:
            df.columns = headers
        
        # Write to Excel
        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Data')
        
        return response
    
    @staticmethod
    def export_to_csv(data, filename, headers=None):
        """Export data to CSV format"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
        
        writer = csv.writer(response)
        
        # Write headers
        if headers:
            writer.writerow(headers)
        
        # Write data
        for row in data:
            writer.writerow(row)
        
        return response
    
    @staticmethod
    def export_to_pdf(data, filename, headers=None, title="Export Report"):
        """Export data to PDF format with Chrome compatibility - FIXED"""
        start_time = time.time()
        export_logger.info(f"📄 PDF Export Started: {filename} - Rows: {len(data)} - Headers: {bool(headers)}")
        
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            elements = []
            
            # Styles
            styles = getSampleStyleSheet()
            title_style = styles['Title']
            
            # Title
            title_para = Paragraph(title, title_style)
            elements.append(title_para)
            
            # Table data
            table_data = []
            if headers:
                table_data.append(headers)
            table_data.extend(data)
            
            export_logger.debug(f"📊 Table Data Prepared: {len(table_data)} rows")
            
            # Create table
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
            doc.build(elements)
            
            # Get PDF content and ensure it's complete
            pdf_content = buffer.getvalue()
            buffer.close()
            
            generation_time = time.time() - start_time
            export_logger.info(f"🔧 PDF Generated: {len(pdf_content)} bytes in {generation_time:.3f}s")
            
            # Validate PDF content
            if not pdf_content or len(pdf_content) < 100:
                export_logger.error(f"❌ PDF Generation Failed: Empty or too small ({len(pdf_content)} bytes)")
                from django.http import HttpResponse
                return HttpResponse('PDF generation failed', status=500)
            
            # ✅ FIXED: Create Chrome-compatible response with correct headers
            from django.http import HttpResponse
            response = HttpResponse(pdf_content, content_type='application/pdf')
            
            # ✅ FIXED: Proper Content-Disposition header format
            response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
            
            # ✅ FIXED: Essential headers for Chrome compatibility
            response['Content-Length'] = str(len(pdf_content))
            response['Accept-Ranges'] = 'bytes'
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            
            total_time = time.time() - start_time
            export_logger.info(f"✅ PDF Export Complete: {filename} - {len(pdf_content)} bytes - {total_time:.3f}s")
            
            # ✅ FIXED: Return response immediately - NO additional responses
            return response
            
        except Exception as e:
            error_time = time.time() - start_time
            export_logger.error(f"❌ PDF Export Error: {filename} - {str(e)} - {error_time:.3f}s")
            raise

    @staticmethod
    def prepare_student_data(students):
        """Prepare student data for export"""
        data = []
        headers = ['Name', 'Admission Number', 'Class', 'Email', 'Mobile', 'Date of Birth']
        
        for student in students:
            data.append([
                f"{student.first_name} {student.last_name}",
                student.admission_number,
                student.class_section.class_name if student.class_section else 'N/A',
                student.email or 'N/A',
                student.mobile_number or 'N/A',
                student.date_of_birth.strftime('%Y-%m-%d') if student.date_of_birth else 'N/A'
            ])
        
        return data, headers
    
    @staticmethod
    def prepare_teacher_data(teachers):
        """Prepare teacher data for export"""
        data = []
        headers = ['Name', 'Mobile', 'Email', 'Qualification', 'Joining Date']
        
        for teacher in teachers:
            data.append([
                teacher.name,
                teacher.mobile or 'N/A',
                teacher.email or 'N/A',
                teacher.qualification or 'N/A',
                teacher.joining_date.strftime('%Y-%m-%d') if teacher.joining_date else 'N/A'
            ])
        
        return data, headers
    
    @staticmethod
    def prepare_fee_data(fees):
        """Prepare fee data for export"""
        data = []
        headers = ['Fee Type', 'Amount', 'Class', 'Description', 'Status']
        
        for fee in fees:
            data.append([
                fee.fee_type or 'N/A',
                f"Rs{fee.amount}",
                fee.student_class.name if fee.student_class else 'N/A',
                fee.description or 'N/A',
                'Active' if fee.is_active else 'Inactive'
            ])
        
        return data, headers