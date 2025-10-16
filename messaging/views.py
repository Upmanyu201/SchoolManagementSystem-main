from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from django.utils.html import escape
from students.models import Student
from teachers.models import Teacher
from subjects.models import ClassSection
from .models import MessageLog, MessageRecipient, MessagingConfig, MSG91Config
from .services import MessagingService, MSG91Service
from users.decorators import module_required
import logging

logger = logging.getLogger(__name__)

# Optional ML integration
try:
    from core.ml_integrations import ml_service
    ML_AVAILABLE = True
except ImportError:
    ml_service = None
    ML_AVAILABLE = False

import json

@login_required
@module_required('messaging', 'view')
def messaging_dashboard(request):
    """Main messaging dashboard showing all contacts with pagination"""
    # Get messaging config
    config = MessagingConfig.get_active_config()
    
    # Get and validate pagination parameters
    try:
        page = int(request.GET.get('page', 1))
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        page = 1
    
    try:
        per_page = int(request.GET.get('per_page', 20))
        if per_page not in [20, 50, 100]:
            per_page = 20
    except (ValueError, TypeError):
        per_page = 20
    
    # Sanitize search and filter parameters
    search = escape(request.GET.get('search', '').strip()[:50])
    role_filter = request.GET.get('role', '')
    if role_filter not in ['Student', 'Teacher', '']:
        role_filter = ''
    class_filter = escape(request.GET.get('class', '').strip()[:50])
    
    # Validation already done above
    
    # Get all students with their contact info
    students_query = Student.objects.all_statuses().select_related('class_section')
    if search:
        students_query = students_query.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(mobile_number__icontains=search) |
            Q(admission_number__icontains=search)
        )
    if class_filter:
        students_query = students_query.filter(class_section__class_name__icontains=class_filter)
    
    student_contacts = []
    for student in students_query:
        student_contacts.append({
            'id': student.id,
            'name': student.get_full_display_name(),
            'phone': student.mobile_number,
            'role': 'Student',
            'class_info': f"{student.class_section.class_name} - {student.class_section.section_name}" if student.class_section else 'N/A',
            'type': 'student'
        })
    
    # Get all teachers with their contact info
    teachers_query = Teacher.objects.all()
    if search:
        teachers_query = teachers_query.filter(
            Q(name__icontains=search) |
            Q(mobile__icontains=search)
        )
    
    teacher_contacts = []
    for teacher in teachers_query:
        teacher_contacts.append({
            'id': teacher.id,
            'name': teacher.name,
            'phone': teacher.mobile,
            'role': 'Teacher',
            'class_info': 'Staff',
            'type': 'teacher'
        })
    
    # Combine and filter contacts
    all_contacts = []
    if not role_filter or role_filter == 'Student':
        all_contacts.extend(student_contacts)
    if not role_filter or role_filter == 'Teacher':
        all_contacts.extend(teacher_contacts)
    
    # Paginate contacts
    paginator = Paginator(all_contacts, per_page)
    contacts_page = paginator.get_page(page)
    
    # Get all classes for filtering
    classes = ClassSection.objects.all()
    
    # Recent message logs
    recent_messages = MessageLog.objects.filter(sender=request.user).order_by('-created_at')[:10]
    
    # ML: Optimize message timing (optional)
    timing_optimization = None
    if ML_AVAILABLE and ml_service:
        messaging_data = {
            'hourly_response_rates': {9: 0.85, 14: 0.78, 18: 0.82}
        }
        timing_optimization = ml_service.optimize_message_timing(messaging_data)
    
    context = {
        'contacts_page': contacts_page,
        'all_contacts': contacts_page.object_list,
        'classes': classes,
        'recent_messages': recent_messages,
        'total_students': len(student_contacts),
        'total_teachers': len(teacher_contacts),
        'total_contacts': len(all_contacts),
        'config': config,
        'current_page': int(page),
        'per_page': per_page,
        'search': search,
        'role_filter': role_filter,
        'class_filter': class_filter,
        'timing_optimization': timing_optimization,
        'best_send_times': timing_optimization['best_send_times'] if timing_optimization else [9, 14, 18],
        'expected_response_rate': timing_optimization['expected_response_rate'] if timing_optimization else '80%',
    }
    
    return render(request, 'messaging/dashboard.html', context)

@login_required
@csrf_protect
@require_POST
@module_required('messaging', 'edit')
def send_individual_message(request):
    """Send message to individual contact"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid data format received'
        })
    
    contact_type = data.get('contact_type')
    contact_id = data.get('contact_id')
    message_type = data.get('message_type')
    message_content = data.get('message')
    
    # Validate inputs
    if contact_type not in ['student', 'teacher']:
        return JsonResponse({
            'success': False,
            'message': 'Invalid contact type selected'
        })
    
    try:
        contact_id_int = int(contact_id)
        if contact_id_int <= 0:
            raise ValidationError("Invalid contact ID")
    except (ValueError, TypeError, ValidationError):
        return JsonResponse({
            'success': False,
            'message': 'Invalid contact information'
        })
    
    if message_type != 'SMS':
        return JsonResponse({
            'success': False,
            'message': 'Only SMS messaging is supported'
        })
    
    # Validate and sanitize message content
    if not message_content or len(message_content.strip()) < 5:
        return JsonResponse({
            'success': False,
            'message': 'Please enter a message (at least 5 characters)'
        })
    
    if len(message_content) > 1000:
        return JsonResponse({
            'success': False,
            'message': 'Message is too long (maximum 1000 characters)'
        })
    
    message_content = escape(message_content.strip())
        
    # Get contact details
    try:
        if contact_type == 'student':
            contact = Student.objects.get(id=contact_id_int)
            phone = contact.mobile_number
            name = contact.get_full_display_name()
            role = 'Student'
        else:
            contact = Teacher.objects.get(id=contact_id_int)
            phone = contact.mobile
            name = contact.name
            role = 'Teacher'
    except (Student.DoesNotExist, Teacher.DoesNotExist):
        return JsonResponse({
            'success': False,
            'message': 'Contact not found'
        })
    
    # Validate phone number
    if not phone or len(phone.strip()) < 10:
        return JsonResponse({
            'success': False,
            'message': f'No valid phone number found for {name}'
        })
        
    try:
        # Log messaging attempt
        logger.info(f"User {request.user.id} sending message to {contact_type} {contact_id_int}")
        
        messaging_service = MessagingService()
        
        # Send SMS
        result = messaging_service.send_sms(phone, message_content)
        
        # Create message log
        message_log = MessageLog.objects.create(
            sender=request.user,
            message_type='SMS',
            recipient_type='INDIVIDUAL',
            message_content=message_content,
            total_recipients=1,
            successful_sends=1 if result['success'] else 0,
            failed_sends=0 if result['success'] else 1,
            status='SENT' if result['success'] else 'FAILED',
            source_module='messaging'
        )
        
        MessageRecipient.objects.create(
            message_log=message_log,
            student=contact if contact_type == 'student' else None,
            teacher=contact if contact_type == 'teacher' else None,
            phone_number=phone,
            name=name,
            role=role,
            status='SENT' if result['success'] else 'FAILED',
            error_message=result.get('error', '')
        )
        
        return JsonResponse({
            'success': result['success'],
            'message': f'Perfect! Your message has been sent to {name}.' if result['success'] else f'Sorry, we couldn\'t send the message to {name}. Please try again.',
            'error': result.get('error', '')
        })
    except Exception as e:
        logger.error(f"Error sending individual message by user {request.user.id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Something went wrong while sending the message. Please try again.'
        })
        
        return JsonResponse({
            'success': result['success'],
            'message': f'Perfect! Your message has been sent to {name}.' if result['success'] else f'Sorry, we couldn\'t send the message to {name}. Please try again.',
            'error': result.get('error', '')
        })
    except Exception as e:
        logger.error(f"Error sending individual message by user {request.user.id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Something went wrong while sending the message. Please try again.'
        })


@login_required
@csrf_protect
@require_POST
@module_required('messaging', 'edit')
def send_bulk_message(request):
    """Send bulk messages"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid data format received'
        })
    
    recipient_type = data.get('recipient_type')
    message_type = data.get('message_type')
    message_content = data.get('message')
    class_id = data.get('class_id')
    
    # Validate inputs
    if recipient_type not in ['ALL_STUDENTS', 'ALL_TEACHERS', 'CLASS_STUDENTS']:
        return JsonResponse({
            'success': False,
            'message': 'Invalid recipient type selected'
        })
    
    if message_type != 'SMS':
        return JsonResponse({
            'success': False,
            'message': 'Only SMS messaging is supported'
        })
    
    # Validate message content
    if not message_content or len(message_content.strip()) < 5:
        return JsonResponse({
            'success': False,
            'message': 'Please enter a message (at least 5 characters)'
        })
    
    if len(message_content) > 1000:
        return JsonResponse({
            'success': False,
            'message': 'Message is too long (maximum 1000 characters)'
        })
    
    message_content = escape(message_content.strip())
    
    # Validate class_id if needed
    if recipient_type == 'CLASS_STUDENTS':
        if not class_id:
            return JsonResponse({
                'success': False,
                'message': 'Please select a class for class-specific messages'
            })
        try:
            class_id_int = int(class_id)
            if class_id_int <= 0:
                raise ValidationError("Invalid class ID")
        except (ValueError, TypeError, ValidationError):
            return JsonResponse({
                'success': False,
                'message': 'Invalid class selection'
            })
        
        recipients = []
        
        # Build recipient list based on type
        if recipient_type == 'ALL_STUDENTS':
            students = Student.objects.all_statuses()            
            for student in students:
                recipients.append({
                    'student': student,
                    'teacher': None,
                    'phone': student.mobile_number,
                    'name': student.get_full_display_name(),
                    'role': 'Student'
                })
        
        elif recipient_type == 'ALL_TEACHERS':
            teachers = Teacher.objects.all()
            for teacher in teachers:
                recipients.append({
                    'student': None,
                    'teacher': teacher,
                    'phone': teacher.mobile,
                    'name': teacher.name,
                    'role': 'Teacher'
                })
        
        elif recipient_type == 'CLASS_STUDENTS' and class_id:
            students = Student.objects.all_statuses().filter(class_section__id=class_id)
            for student in students:
                recipients.append({
                    'student': student,
                    'teacher': None,
                    'phone': student.mobile_number,
                    'name': student.get_full_display_name(),
                    'role': 'Student'
                })
        
        if not recipients:
            return JsonResponse({'success': False, 'message': 'No contacts found to send messages to. Please check your selection.'})
        
        # Create message log
        message_log = MessageLog.objects.create(
            sender=request.user,
            message_type=message_type,
            recipient_type=recipient_type,
            message_content=message_content,
            total_recipients=len(recipients),
            source_module='messaging',
            class_section_filter_id=class_id if class_id else None
        )
        
        messaging_service = MessagingService()
        
        if message_type == 'SMS':
            # Send bulk SMS
            results = messaging_service.send_bulk_sms(recipients, message_content, message_log)
            
            return JsonResponse({
                'success': True,
                'message': f'Great! Your message has been sent to {message_log.successful_sends} out of {len(recipients)} contacts.',
                'successful': message_log.successful_sends,
                'failed': message_log.failed_sends
            })
    
    return JsonResponse({'success': False, 'message': 'Please use the bulk messaging form to send messages to multiple contacts.'})

@module_required('messaging', 'view')
def get_class_students(request):
    """Get students for a specific class"""
    class_id = request.GET.get('class_id')
    if class_id:
        students = Student.objects.all_statuses().filter(class_section__id=class_id).select_related('class_section')
        student_list = []
        for student in students:
            student_list.append({
                'id': student.id,
                'name': student.get_full_display_name(),
                'phone': student.mobile_number,
                'section': student.class_section.section_name if student.class_section else 'N/A'
            })
        return JsonResponse({'students': student_list})
    return JsonResponse({'students': []})

@module_required('messaging', 'view')
def message_history(request):
    """View message history from all modules"""
    # Get filter parameters
    source_filter = request.GET.get('source', '')
    status_filter = request.GET.get('status', '')
    
    # Base query - show all messages from all modules
    message_logs = MessageLog.objects.all()
    
    # Apply filters
    if source_filter and source_filter != 'all':
        message_logs = message_logs.filter(source_module=source_filter)
    if status_filter and status_filter != 'all':
        message_logs = message_logs.filter(status=status_filter)
    
    # Order by most recent
    message_logs = message_logs.order_by('-created_at')
    
    # Get filter options
    source_modules = MessageLog.SOURCE_MODULE_CHOICES
    status_choices = MessageLog.STATUS_CHOICES
    
    context = {
        'message_logs': message_logs,
        'source_modules': source_modules,
        'status_choices': status_choices,
        'current_source_filter': source_filter,
        'current_status_filter': status_filter,
    }
    
    return render(request, 'messaging/history.html', context)

@module_required('messaging', 'view')
def message_details(request, message_id):
    """View details of a specific message"""
    message_log = MessageLog.objects.get(id=message_id, sender=request.user)
    recipients = MessageRecipient.objects.filter(message_log=message_log)
    
    context = {
        'message_log': message_log,
        'recipients': recipients
    }
    return render(request, 'messaging/details.html', context)

@module_required('messaging', 'edit')
def messaging_config(request):
    """Configure messaging settings"""
    config = MessagingConfig.get_active_config()
    msg91_config = MSG91Config.get_active_config()
    
    if request.method == 'POST':
        # Basic Configuration
        sender_name = request.POST.get('sender_name')
        sender_phone = request.POST.get('sender_phone')
        sms_enabled = request.POST.get('sms_enabled') == 'on'
        
        # MSG91 Configuration
        msg91_auth_key = request.POST.get('msg91_auth_key')
        msg91_sender_id = request.POST.get('msg91_sender_id', 'TXTLCL')
        msg91_enabled = request.POST.get('msg91_enabled') == 'on'
        
        if config:
            # Update existing config
            config.sender_name = sender_name
            config.sender_phone = sender_phone
            config.sms_enabled = sms_enabled
            config.save()
        else:
            # Create new config
            config = MessagingConfig.objects.create(
                sender_name=sender_name,
                sender_phone=sender_phone,
                sms_enabled=sms_enabled,
                is_active=True
            )
        
        # Handle MSG91 Configuration
        if msg91_auth_key:
            if msg91_config:
                # Update existing MSG91 config
                msg91_config.auth_key = msg91_auth_key
                msg91_config.sender_id = msg91_sender_id
                msg91_config.is_active = msg91_enabled
                msg91_config.save()
            else:
                # Create new MSG91 config
                msg91_config = MSG91Config.objects.create(
                    auth_key=msg91_auth_key,
                    sender_id=msg91_sender_id,
                    is_active=msg91_enabled
                )
        
        messages.success(request, 'Perfect! Your messaging settings have been updated successfully.')
        return redirect('messaging:config')
    
    context = {
        'config': config,
        'msg91_config': msg91_config
    }
    return render(request, 'messaging/config.html', context)

@login_required
@csrf_protect
@require_POST
def test_sms(request):
    """Test SMS endpoint for MSG91"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid data format received'
        })
    
    phone = data.get('phone', '919876543210')
    message = data.get('message', 'Test SMS from School Management System')
    
    # Validate phone number
    if not phone or len(phone.strip()) < 10:
        return JsonResponse({
            'success': False,
            'error': 'Please provide a valid phone number'
        })
    
    # Sanitize phone number (remove non-digits)
    clean_phone = ''.join(filter(str.isdigit, phone))
    if len(clean_phone) < 10:
        return JsonResponse({
            'success': False,
            'error': 'Phone number must be at least 10 digits'
        })
    
    # Validate and sanitize message
    if not message or len(message.strip()) < 5:
        return JsonResponse({
            'success': False,
            'error': 'Test message must be at least 5 characters'
        })
    
    message = escape(message.strip()[:160])  # Limit to SMS length
            
    try:
        # Log test SMS attempt
        logger.info(f"User {request.user.id} testing SMS to {clean_phone}")
        
        # Test MSG91 service
        service = MSG91Service()
        result = service.send_sms(clean_phone, message)
        
        return JsonResponse({
            'success': result['success'],
            'message': 'Great! Test message sent successfully.' if result['success'] else 'Sorry, the test message failed to send. Please check your settings.',
            'details': result,
            'phone': clean_phone
        })
        
    except Exception as e:
        logger.error(f"Error testing SMS by user {request.user.id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Something went wrong while testing the SMS service. Please check your configuration.'
        })


@login_required
@module_required('messaging', 'edit')
def test_page(request):
    """MSG91 test page"""
    try:
        return render(request, 'messaging/test_msg91.html')
    except Exception as e:
        logger.error(f"Error loading test page for user {request.user.id}: {str(e)}")
        messages.error(request, "We're having trouble loading the test page. Please try again.")
        return redirect('messaging:dashboard')