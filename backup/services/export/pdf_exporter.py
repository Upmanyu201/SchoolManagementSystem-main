# backup/services/export/pdf_exporter.py
"""PDF export functionality"""

import io
import logging
import time
from datetime import datetime
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied, ValidationError
from collections import defaultdict

from .base import DataExportService
from .constants import ExportConstants
from .row_formatters import RowFormatter

export_logger = logging.getLogger('export.api')

try:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

class PDFExporter(DataExportService):
    """PDF export service"""
    
    @classmethod
    def export_to_pdf(cls, module_name, user):
        """Export data to PDF format with enhanced security and performance"""
        start_time = time.time()
        
        try:
            cls._validate_user_permissions(user, module_name)
            
            data = cls.get_module_data(module_name)
            if len(data) > ExportConstants.MAX_RECORDS_PDF:
                raise ValidationError(f"Dataset too large for PDF: {len(data)} records. Maximum allowed: {ExportConstants.MAX_RECORDS_PDF}")
            
            export_logger.info(f"PDF Export Started: {module_name} - {len(data)} records - User: {user.username}")
            
            return cls._generate_pdf_response(module_name, data, user, start_time)
            
        except (PermissionDenied, ValidationError) as e:
            export_logger.warning(f"PDF export denied for {module_name}: {e} - User: {user.username}")
            return HttpResponse(str(e), status=403)
        except Exception as e:
            export_logger.error(f"PDF export failed for {module_name}: {e}")
            return HttpResponse(f'PDF export failed: {str(e)}', status=500)
    
    @classmethod
    def _generate_pdf_response(cls, module_name, data, user, start_time):
        """Generate PDF response with proper resource management"""
        try:
            if not PDF_AVAILABLE:
                export_logger.warning(f"PDF library unavailable, falling back to CSV for {module_name}")
                from .csv_exporter import CSVExporter
                return CSVExporter.export_to_csv(module_name, user)
            
            buffer = io.BytesIO()
            doc = cls._setup_pdf_document(buffer)
            
            elements = []
            styles, title_style = cls._create_pdf_styles()
            
            cls._generate_pdf_content(elements, module_name, data, user, styles, title_style)
            
            generation_start = time.time()
            doc.build(elements)
            generation_time = time.time() - generation_start
            export_logger.debug(f"PDF generation completed in {generation_time:.3f}s")
            
            response = cls._create_pdf_response(buffer, module_name, user, start_time)
            buffer.close()
            
            return response
            
        except Exception as e:
            export_logger.error(f"PDF generation error for {module_name}: {e}")
            return HttpResponse(f'PDF export failed: {str(e)}', status=500)
    
    @classmethod
    def _setup_pdf_document(cls, buffer):
        """Setup PDF document with proper configuration for wide tables"""
        return SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=0.3*inch,
            leftMargin=0.3*inch,
            topMargin=0.5*inch,
            bottomMargin=0.3*inch
        )
    
    @classmethod
    def _create_pdf_styles(cls):
        """Create PDF styles"""
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            alignment=1,
            textColor=colors.darkblue
        )
        return styles, title_style
    
    @classmethod
    def _generate_pdf_content(cls, elements, module_name, data, user, styles, title_style):
        """Generate PDF content elements"""
        current_time = datetime.now()
        
        # Title
        title = Paragraph(f"{module_name.title()} Export Report", title_style)
        elements.append(title)
        
        # Metadata
        meta_style = ParagraphStyle(
            'MetaStyle',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=15
        )
        meta_text = f"Generated on {current_time.strftime('%Y-%m-%d %H:%M:%S')} by {user.username} | Total Records: {len(data)}"
        elements.append(Paragraph(meta_text, meta_style))
        elements.append(Spacer(1, 12))
        
        if module_name == 'students' and data:
            cls._create_students_pdf_by_class(elements, data)
        elif module_name == 'fees_report' and data:
            cls._create_fees_report_pdf_by_class(elements, data)
        elif data:
            cls._create_standard_pdf_table(elements, module_name, data)
        else:
            no_data = Paragraph("No data available for export.", styles['Normal'])
            elements.append(no_data)
    
    @classmethod
    def _create_students_pdf_by_class(cls, elements, students):
        """Create PDF with students organized by class"""
        class_groups = cls._group_students_by_class(students)
        sorted_classes = cls._sort_classes(class_groups.keys())
        
        for class_name in sorted_classes:
            if not class_groups[class_name]:
                continue
            
            cls._create_class_section(elements, class_name, class_groups[class_name])
            
            if class_name != sorted_classes[-1]:
                elements.append(PageBreak())
    
    @classmethod
    def _create_fees_report_pdf_by_class(cls, elements, fee_data):
        """Create PDF with fee report organized by class"""
        class_groups = cls._group_fee_report_by_class(fee_data)
        sorted_classes = cls._sort_classes(class_groups.keys())
        
        for class_name in sorted_classes:
            if not class_groups[class_name]:
                continue
            
            cls._create_fee_report_class_section(elements, class_name, class_groups[class_name])
            
            if class_name != sorted_classes[-1]:
                elements.append(PageBreak())
    
    @classmethod
    def _group_fee_report_by_class(cls, fee_data):
        """Group fee report data by class"""
        class_groups = defaultdict(list)
        for row in fee_data:
            try:
                class_name = getattr(row, 'class_name', 'Unassigned') or 'Unassigned'
                class_groups[class_name].append(row)
            except AttributeError:
                class_groups['Unassigned'].append(row)
        
        return class_groups
    
    @classmethod
    def _create_fee_report_class_section(cls, elements, class_name, fee_rows):
        """Create a fee report class section in PDF"""
        styles = getSampleStyleSheet()
        class_style = ParagraphStyle(
            'ClassHeader',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=10,
            textColor=colors.darkblue
        )
        
        # Calculate totals for the class
        total_due = sum(getattr(row, 'final_due', 0) for row in fee_rows)
        paid_count = sum(1 for row in fee_rows if getattr(row, 'final_due', 0) == 0)
        
        class_header = Paragraph(
            f"{class_name} ({len(fee_rows)} students, {paid_count} paid, Total Due: Rs{total_due:.2f})", 
            class_style
        )
        elements.append(class_header)
        
        table = cls._create_fee_report_table(fee_rows)
        elements.append(table)
        elements.append(Spacer(1, 15))
    
    @classmethod
    def _create_fee_report_table(cls, fee_rows):
        """Create fee report table"""
        compact_headers = [
            'Name', 'Adm. No.', 'Total Fees', 'Paid', 'Discount', 'CF Due', 'Fine', 'Final Due', 'Status'
        ]
        
        table_data = [compact_headers]
        
        try:
            sorted_rows = sorted(fee_rows, key=lambda r: getattr(r, 'name', '') or '')
        except AttributeError:
            sorted_rows = fee_rows
        
        for row in sorted_rows:
            try:
                table_row = [
                    str(getattr(row, 'name', ''))[:15],
                    str(getattr(row, 'admission_number', ''))[:10],
                    f"Rs.{getattr(row, 'current_fees', 0):.0f}",
                    f"Rs.{getattr(row, 'current_paid', 0):.0f}",
                    f"Rs.{getattr(row, 'current_discount', 0):.0f}",
                    f"Rs.{getattr(row, 'cf_due', 0):.0f}",
                    f"Rs.{getattr(row, 'fine_unpaid', 0):.0f}",
                    f"Rs.{getattr(row, 'final_due', 0):.0f}",
                    'Paid' if getattr(row, 'final_due', 0) == 0 else 'Due'
                ]
                table_data.append(table_row)
            except Exception as e:
                export_logger.warning(f"Error processing fee report row: {e}")
                continue
        
        # Adjusted column widths for fee report
        col_widths = [1.5*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.6*inch]
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(cls._get_fee_report_table_style())
        
        return table
    
    @classmethod
    def _get_fee_report_table_style(cls):
        """Get fee report table style configuration"""
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 1), (-2, -1), 'RIGHT'),  # Right align amounts
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ])
    
    @classmethod
    def _group_students_by_class(cls, students):
        """Group students by class with safe attribute access"""
        class_groups = defaultdict(list)
        for student in students:
            try:
                if hasattr(student, 'class_section') and student.class_section:
                    class_name = getattr(student.class_section, 'class_name', 'Unknown')
                    class_groups[class_name].append(student)
                else:
                    class_groups['Unassigned'].append(student)
            except AttributeError as e:
                export_logger.warning(f"Error grouping student: {e}")
                class_groups['Unassigned'].append(student)
        
        return class_groups
    
    @classmethod
    def _sort_classes(cls, class_names):
        """Sort class names safely"""
        def get_class_order(class_name):
            if not class_name:
                return (999, 'Unassigned')
            
            class_name = class_name.upper()
            if 'NURSERY' in class_name:
                return (0, 'Nursery')
            elif 'LKG' in class_name:
                return (1, 'LKG')
            elif 'UKG' in class_name:
                return (2, 'UKG')
            elif 'CLASS' in class_name or 'STD' in class_name:
                try:
                    import re
                    match = re.search(r'(\d+)', class_name)
                    if match:
                        num = int(match.group(1))
                        return (2 + num, f'Class {num}')
                except:
                    pass
            return (900, class_name)
        
        return sorted(class_names, key=get_class_order)
    
    @classmethod
    def _create_class_section(cls, elements, class_name, students):
        """Create a class section in PDF"""
        styles = getSampleStyleSheet()
        class_style = ParagraphStyle(
            'ClassHeader',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=10,
            textColor=colors.darkblue
        )
        
        class_header = Paragraph(f"{class_name} ({len(students)} students)", class_style)
        elements.append(class_header)
        
        table = cls._create_students_table(students)
        elements.append(table)
        elements.append(Spacer(1, 15))
    
    @classmethod
    def _create_students_table(cls, students):
        """Create students table with bulk fee calculation"""
        compact_headers = [
            'Adm. No.', 'Name', 'Father Name', 'Mother Name', 'Class', 'Mobile', 'Final Due'
        ]
        
        table_data = [compact_headers]
        
        # Get fee report data for Final Due calculations
        fee_report_data = cls._get_fee_report_data()
        fee_lookup = {row.student_id: row.final_due for row in fee_report_data}
        
        try:
            sorted_students = sorted(students, key=lambda s: (
                getattr(s, 'first_name', ''), 
                getattr(s, 'last_name', '')
            ))
        except AttributeError:
            sorted_students = students
        
        for student in sorted_students:
            row = cls._create_student_row(student, fee_lookup)
            table_data.append(row)
        
        col_widths = [w*inch for w in ExportConstants.STUDENT_COL_WIDTHS]
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(cls._get_table_style())
        
        return table
    
    @classmethod
    def _create_student_row(cls, student, fee_lookup):
        """Create a single student row with safe attribute access"""
        return RowFormatter.format_student_row_compact(student, fee_lookup)
    
    @classmethod
    def _get_table_style(cls):
        """Get table style configuration"""
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('ALIGN', (3, 1), (4, -1), 'CENTER'),
        ])
    
    @classmethod
    def _create_standard_pdf_table(cls, elements, module_name, data):
        """Create standard PDF table for non-student modules"""
        headers = ExportConstants.CSV_HEADERS.get(module_name, ['Data'])
        
        # Process data in chunks for better performance
        limited_data = data[:ExportConstants.PDF_CHUNK_SIZE] if len(data) > ExportConstants.PDF_CHUNK_SIZE else data
        
        table_data = [headers]
        
        for item in limited_data:
            try:
                if module_name == 'teachers':
                    row_data = RowFormatter.format_teacher_row(item)
                elif module_name == 'subjects':
                    # Handle multiple rows returned by format_subject_row
                    rows = RowFormatter.format_subject_row(item)
                    # For PDF, add all rows for this class section
                    if isinstance(rows, list) and len(rows) > 0 and isinstance(rows[0], list):
                        for row in rows:
                            # Truncate long text for PDF display
                            truncated_row = []
                            for cell in row:
                                cell_str = str(cell)
                                if len(cell_str) > 15:
                                    truncated_row.append(cell_str[:12] + '...')
                                else:
                                    truncated_row.append(cell_str)
                            table_data.append(truncated_row)
                        continue  # Skip the normal row processing
                    else:
                        row_data = rows
                elif module_name == 'transport':
                    row_data = RowFormatter.format_transport_row(item)
                elif module_name == 'fees':
                    row_data = RowFormatter.format_fees_row(item)
                elif module_name == 'student_fees':
                    row_data = RowFormatter.format_student_fees_row(item)

                elif module_name == 'attendance':
                    row_data = RowFormatter.format_attendance_row(item)


                elif module_name == 'users':
                    row_data = RowFormatter.format_users_row(item)
                elif module_name == 'fees_report':
                    row_data = RowFormatter.format_fees_report_row(item)
                else:
                    row_data = [str(item)]
                
                # Truncate long text for PDF display
                truncated_row = []
                for cell in row_data:
                    cell_str = str(cell)
                    if len(cell_str) > 15:
                        truncated_row.append(cell_str[:12] + '...')
                    else:
                        truncated_row.append(cell_str)
                table_data.append(truncated_row)
            except Exception as e:
                export_logger.warning(f"Error processing item for PDF: {e}")
                continue
        
        # Dynamic column widths
        num_cols = len(headers)
        available_width = 10 * inch
        col_width = available_width / num_cols
        col_widths = [col_width] * num_cols
        
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        elements.append(table)
        
        # Add note if data was limited
        if len(data) > ExportConstants.PDF_CHUNK_SIZE:
            styles = getSampleStyleSheet()
            note = Paragraph(
                f"Note: Showing first {ExportConstants.PDF_CHUNK_SIZE} of {len(data)} records for PDF optimization.", 
                styles['Normal']
            )
            elements.append(Spacer(1, 10))
            elements.append(note)
    
    @classmethod
    def _create_pdf_response(cls, buffer, module_name, user, start_time):
        """Create HTTP response for PDF"""
        try:
            pdf_content = buffer.getvalue()
            
            if not pdf_content or len(pdf_content) < 100:
                raise ValueError(f"PDF validation failed: {len(pdf_content)} bytes")
            
            export_logger.info(f"PDF content validated: {len(pdf_content)} bytes for {module_name}")
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            filename = cls._sanitize_filename(f"{module_name}_export_{timestamp}.pdf")
            
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="{filename}"'
            response['Content-Length'] = len(pdf_content)
            response['Accept-Ranges'] = 'bytes'
            response['X-Content-Type-Options'] = 'nosniff'
            response['Cache-Control'] = 'public, max-age=300'
            response['X-PDF-Viewer'] = 'chrome-native'
            
            total_time = time.time() - start_time
            export_logger.info(
                f"PDF Export Complete: {module_name} - {filename} - "
                f"{len(pdf_content)} bytes - {total_time:.3f}s - User: {user.username}"
            )
            
            return response
            
        except Exception as e:
            export_logger.error(f"PDF response creation failed: {e}")
            raise