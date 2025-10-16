from django.db import models
from django.contrib.auth import get_user_model
from students.models import Student
from teachers.models import Teacher
from core.models import BaseModel

User = get_user_model()

class MSG91Config(BaseModel):
    """MSG91 SMS Configuration"""
    auth_key = models.CharField(max_length=100, help_text="MSG91 Auth Key")
    sender_id = models.CharField(max_length=10, default="TXTLCL", help_text="MSG91 Sender ID")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "MSG91 Configuration"
    
    def __str__(self):
        return f"MSG91 Config - {self.sender_id}"
    
    @classmethod
    def get_active_config(cls):
        return cls.objects.filter(is_active=True).first()

class MessagingConfig(BaseModel):
    """Basic Messaging Configuration"""
    sender_name = models.CharField(max_length=100, default="School")
    sender_phone = models.CharField(max_length=15, default="")
    sms_enabled = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    @classmethod
    def get_active_config(cls):
        return cls.objects.filter(is_active=True).first()

class MessageLog(BaseModel):
    STATUS_CHOICES = [
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
        ('PENDING', 'Pending'),
    ]
    
    MESSAGE_TYPE_CHOICES = [
        ('SMS', 'SMS'),
    ]
    
    RECIPIENT_TYPE_CHOICES = [
        ('INDIVIDUAL', 'Individual'),
        ('ALL_STUDENTS', 'All Students'),
        ('ALL_TEACHERS', 'All Teachers'),
        ('CLASS_STUDENTS', 'Class Students'),
    ]
    
    SOURCE_MODULE_CHOICES = [
        ('messaging', 'Messaging'),
        ('student_fees', 'Student Fees'),
        ('reports', 'Reports'),
        ('attendance', 'Attendance'),
        ('transport', 'Transport'),
        ('fines', 'Fines'),
        ('system', 'System'),
    ]
    
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES, default='SMS')
    recipient_type = models.CharField(max_length=20, choices=RECIPIENT_TYPE_CHOICES, default='INDIVIDUAL')
    message_content = models.TextField()
    total_recipients = models.IntegerField(default=0)
    successful_sends = models.IntegerField(default=0)
    failed_sends = models.IntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    source_module = models.CharField(max_length=20, choices=SOURCE_MODULE_CHOICES, default='messaging')
    class_section_filter = models.ForeignKey('subjects.ClassSection', on_delete=models.CASCADE, null=True, blank=True)
    
    # Legacy fields for backward compatibility
    recipient_phone = models.CharField(max_length=15, blank=True)
    recipient_name = models.CharField(max_length=100, blank=True)
    msg91_message_id = models.CharField(max_length=100, blank=True)
    error_message = models.TextField(blank=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return f"{self.get_source_module_display()} - {self.message_type} to {self.recipient_type} - {self.status}"

class MessageRecipient(BaseModel):
    """Individual message recipients"""
    STATUS_CHOICES = [
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
        ('PENDING', 'Pending'),
    ]
    
    message_log = models.ForeignKey(MessageLog, on_delete=models.CASCADE, related_name='recipients')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, null=True, blank=True)
    phone_number = models.CharField(max_length=15)
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=20, default='Student')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    error_message = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.name} - {self.status}"

class MessageTemplate(BaseModel):
    """Message templates for reusable messages"""
    MESSAGE_TYPE_CHOICES = [
        ('fee_reminder', 'Fee Reminder'),
        ('attendance', 'Attendance Alert'),
        ('general', 'General Notice'),
        ('exam', 'Exam Notification'),
        ('event', 'Event Announcement'),
    ]
    
    name = models.CharField(max_length=100)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='general')
    template_content = models.TextField(help_text="Use variables like {{ student_name }}, {{ amount }}, etc.")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name