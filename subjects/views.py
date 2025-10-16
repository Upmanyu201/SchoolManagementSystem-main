from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from .models import ClassSection, Subject, SubjectAssignment
from .forms import ClassSectionForm, SubjectForm, SubjectAssignmentForm
from users.decorators import module_required
import csv
import io
import codecs

@module_required('subjects', 'view')
def subjects_management(request):
    # Get all data with proper ordering
    class_sections = ClassSection.objects.all().order_by('class_name', 'section_name')
    subjects = Subject.objects.all().order_by('name')
    assignments = SubjectAssignment.objects.select_related('class_section', 'subject').all()
    
    context = {
        'class_sections': class_sections,
        'subjects': subjects,
        'assignments': assignments,
    }
    return render(request, 'subjects/subjects_management.html', context)

@module_required('classes', 'edit')
def add_class_section(request):
    if request.method == 'POST':
        form = ClassSectionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Great! Class {form.cleaned_data["class_name"]}-{form.cleaned_data["section_name"]} has been created successfully.')
            return redirect('subjects_management')
    else:
        form = ClassSectionForm()
    return render(request, 'subjects/add_class_section.html', {'form': form})

@module_required('classes', 'edit')
def edit_class_section(request, pk):
    class_section = get_object_or_404(ClassSection, pk=pk)
    if request.method == 'POST':
        form = ClassSectionForm(request.POST, instance=class_section)
        if form.is_valid():
            form.save()
            messages.success(request, f'Perfect! {class_section.display_name} has been updated successfully.')
            return redirect('subjects_management')
    else:
        form = ClassSectionForm(instance=class_section)
    return render(request, 'subjects/edit_class_section.html', {'form': form, 'class_section': class_section})

@module_required('classes', 'edit')
def delete_class_section(request, pk):
    class_section = get_object_or_404(ClassSection, pk=pk)
    if request.method == 'POST':
        # Check if any students are assigned to this class section
        student_count = class_section.students.count()
        if student_count > 0:
            messages.error(request, f'Sorry, we can\'t delete this class section because {student_count} students are still assigned to it. Please move the students first.')
        else:
            class_section.delete()
            messages.success(request, f'{class_section.display_name} has been removed successfully.')
    return redirect('subjects_management')

@module_required('subjects', 'edit')
def add_subject(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Great! Subject "{form.cleaned_data["name"]}" has been added successfully.')
            return redirect('subjects_management')
    else:
        form = SubjectForm()
    return render(request, 'subjects/add_subject.html', {'form': form})

@module_required('subjects', 'edit')
def edit_subject(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            messages.success(request, f'Perfect! Subject "{subject.name}" has been updated successfully.')
            return redirect('subjects_management')
    else:
        form = SubjectForm(instance=subject)
    return render(request, 'subjects/edit_subject.html', {'form': form, 'subject': subject})

@module_required('subjects', 'edit')
def delete_subject(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        subject.delete()
        messages.success(request, f'Subject "{subject.name}" has been removed successfully.')
    return redirect('subjects_management')

@module_required('subjects', 'edit')
def add_subject_assignment(request):
    if request.method == 'POST':
        form = SubjectAssignmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Great! The subject has been assigned to the class successfully.')
            return redirect('subjects_management')
    else:
        form = SubjectAssignmentForm()
    return render(request, 'subjects/add_subject_assignment.html', {'form': form})

@module_required('subjects', 'edit')
def edit_subject_assignment(request, pk):
    assignment = get_object_or_404(SubjectAssignment, pk=pk)
    if request.method == 'POST':
        form = SubjectAssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfect! The subject assignment has been updated successfully.')
            return redirect('subjects_management')
    else:
        form = SubjectAssignmentForm(instance=assignment)
    return render(request, 'subjects/edit_subject_assignment.html', {'form': form, 'assignment': assignment})

@module_required('subjects', 'edit')
def delete_subject_assignment(request, pk):
    assignment = get_object_or_404(SubjectAssignment, pk=pk)
    if request.method == 'POST':
        assignment.delete()
        messages.success(request, 'The subject assignment has been removed successfully.')
    return redirect('subjects_management')

@module_required('subjects', 'edit')
def import_csv(request):
    """Import subjects from CSV file with proper UTF-8 encoding support."""
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        
        try:
            # Detect encoding and read file
            file_data = csv_file.read()
            
            # Try UTF-8 first, then UTF-8 with BOM, then other encodings
            encodings = ['utf-8-sig', 'utf-8', 'latin1', 'cp1252']
            decoded_data = None
            
            for encoding in encodings:
                try:
                    decoded_data = file_data.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if not decoded_data:
                return JsonResponse({'success': False, 'message': 'We couldn\'t read your file. Please make sure it\'s saved in UTF-8 format and try again.'})
            
            # Parse CSV
            csv_reader = csv.reader(io.StringIO(decoded_data))
            
            imported_count = 0
            errors = []
            current_section = None
            
            for row_num, row in enumerate(csv_reader, 1):
                if not row or not any(row):  # Skip empty rows
                    continue
                
                # Check for section headers
                if len(row) == 1 or 'data' in row[0].lower():
                    current_section = row[0].lower()
                    continue
                
                # Skip header rows
                if any(header in row[0].lower() for header in ['subject', 'class', 'name']):
                    continue
                
                try:
                    if 'subject management' in str(current_section):
                        # Import subjects
                        if len(row) >= 1 and row[0].strip():
                            subject_name = row[0].strip()
                            subject, created = Subject.objects.get_or_create(name=subject_name)
                            if created:
                                imported_count += 1
                    
                    elif 'class-section' in str(current_section):
                        # Import class sections
                        if len(row) >= 2 and row[0].strip() and row[1].strip():
                            class_name = row[0].strip()
                            section_name = row[1].strip()
                            room_number = row[2].strip() if len(row) > 2 else ''
                            
                            cs, created = ClassSection.objects.get_or_create(
                                class_name=class_name,
                                section_name=section_name,
                                defaults={'room_number': room_number}
                            )
                            if created:
                                imported_count += 1
                
                except Exception as e:
                    errors.append(f'Row {row_num}: {str(e)}')
            
            if errors:
                return JsonResponse({
                    'success': False, 
                    'message': f'Import completed! We added {imported_count} records, but encountered {len(errors)} issues that need your attention.',
                    'errors': errors[:10]  # Show first 10 errors
                })
            
            return JsonResponse({
                'success': True, 
                'message': f'Excellent! We successfully imported {imported_count} records from your file.'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'Something went wrong during the import. Please check your file format and try again.'})
    
    return JsonResponse({'success': False, 'message': 'Please select a CSV file to import.'})