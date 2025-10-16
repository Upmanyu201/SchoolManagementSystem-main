from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import View, ListView
from django.http import JsonResponse
from django.db.models import Q
from students.models import Student
from subjects.models import ClassSection as StudentClass
from .models import MessageLog, MessageRecipient, MessagingConfig
from .enhanced_forms import CustomMessageForm, MessageTemplateForm, BulkMessageForm
from .service.notification_service import notification_service
import json

class SendMessageView(LoginRequiredMixin, View):
    """View for sending custom messages"""
    
    def get(self, request):
        form = CustomMessageForm()
        context = {
            'form': form,
            'students': Student.objects.all().order_by('first_name'),
            'classes': StudentClass.objects.all().order_by('class_name'),
            'page_title': 'Send Custom Message'
        }
        return render(request, 'messaging/send_message.html', context)
    
    def post(self, request):
        form = CustomMessageForm(request.POST)
        
        if form.is_valid():
            try:
                recipients = self._get_recipients(form.cleaned_data)
                
                if not recipients:
                    messages.error(request, "No valid recipients found.")
                    return redirect('messaging:send_message')
                
                # Send messages
                results = notification_service.send_custom_message(
                    recipients=recipients,
                    message=form.cleaned_data['message'],
                    provider=form.cleaned_data['provider'] if form.cleaned_data['provider'] != 'auto' else None
                )
                
                # Count results
                sent_count = sum(1 for r in results if r['success'])
                failed_count = len(results) - sent_count
                
                if sent_count > 0:
                    messages.success(request, f"Message sent successfully to {sent_count} recipients.")
                
                if failed_count > 0:
                    messages.warning(request, f"Failed to send message to {failed_count} recipients.")
                
            except Exception as e:
                messages.error(request, f"Error sending message: {str(e)}")
        
        else:
            messages.error(request, "Please correct the form errors.")
        
        return redirect('messaging:send_message')
    
    def _get_recipients(self, cleaned_data):
        """Get recipient phone numbers based on form data"""
        recipients = []
        recipient_type = cleaned_data['recipient_type']
        send_to_parents = cleaned_data['send_to_parents']
        
        if recipient_type == 'individual':
            student = cleaned_data['individual_student']
            if student and student.mobile_number:
                recipients.append(student.mobile_number)
        
        elif recipient_type == 'class':
            student_class = cleaned_data['student_class']
            if student_class:
                students = Student.objects.filter(class_section=student_class)
                if send_to_parents:
                    students = students.exclude(mobile_number__isnull=True).exclude(mobile_number='')
                recipients.extend([s.mobile_number for s in students if s.mobile_number])
        
        elif recipient_type == 'multiple':
            students = cleaned_data['selected_students']
            if send_to_parents:
                students = students.exclude(mobile_number__isnull=True).exclude(mobile_number='')
            recipients.extend([s.mobile_number for s in students if s.mobile_number])
        
        elif recipient_type == 'all':
            students = Student.objects.all()
            if send_to_parents:
                students = students.exclude(mobile_number__isnull=True).exclude(mobile_number='')
            recipients.extend([s.mobile_number for s in students if s.mobile_number])
        
        return list(set(recipients))  # Remove duplicates

class MessageHistoryView(LoginRequiredMixin, ListView):
    """View for message history"""
    
    model = MessageLog
    template_name = 'messaging/message_history.html'
    context_object_name = 'messages'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = MessageLog.objects.all()
        
        # Filter by message type
        message_type = self.request.GET.get('message_type')
        if message_type:
            queryset = queryset.filter(message_type=message_type)
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Search by recipient
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(recipients__phone_number__icontains=search) |
                Q(message_content__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message_types'] = MessageLog.MESSAGE_TYPE_CHOICES
        context['status_choices'] = MessageLog.STATUS_CHOICES
        context['current_filters'] = {
            'message_type': self.request.GET.get('message_type', ''),
            'status': self.request.GET.get('status', ''),
            'search': self.request.GET.get('search', ''),
        }
        return context

@login_required
def get_students_by_class(request):
    """AJAX endpoint to get students by class"""
    class_id = request.GET.get('class_id')
    
    if class_id:
        students = Student.objects.filter(class_section_id=class_id).values(
            'id', 'first_name', 'last_name', 'admission_number', 'mobile_number'
        )
        return JsonResponse({'students': list(students)})
    
    return JsonResponse({'students': []})

@login_required
def messaging_dashboard(request):
    """Messaging dashboard with statistics"""
    from django.utils import timezone
    
    # Get statistics
    total_messages = MessageLog.objects.count()
    today_messages = MessageLog.objects.filter(created_at__date=timezone.now().date()).count()
    failed_messages = MessageLog.objects.filter(status='FAILED').count()
    
    # Recent messages
    recent_messages = MessageLog.objects.all()[:10]
    
    # Message type distribution
    message_type_stats = {}
    for msg_type, display_name in MessageLog.MESSAGE_TYPE_CHOICES:
        count = MessageLog.objects.filter(message_type=msg_type).count()
        message_type_stats[display_name] = count
    
    context = {
        'total_messages': total_messages,
        'today_messages': today_messages,
        'failed_messages': failed_messages,
        'recent_messages': recent_messages,
        'message_type_stats': message_type_stats,
        'page_title': 'Messaging Dashboard'
    }
    
    return render(request, 'messaging/dashboard.html', context)