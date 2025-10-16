# messaging/forms.py
from django import forms
from .models import MessageLog, MessagingConfig
from students.models import Student
from subjects.models import ClassSection
from django.core.exceptions import ValidationError

class MessageForm(forms.ModelForm):
    class Meta:
        model = MessageLog
        fields = ['message_type', 'message_content', 'class_filter']
        widgets = {
            'message_type': forms.Select(attrs={
                'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'message_content': forms.Textarea(attrs={
                'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 4,
                'placeholder': 'Enter your message here...'
            }),
            'class_filter': forms.Select(attrs={
                'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
            })
        }

class BulkMessageForm(forms.Form):
    MESSAGE_TYPE_CHOICES = [
        ('SMS', 'SMS'),
        ('WhatsApp', 'WhatsApp'),
        ('Both', 'Both')
    ]
    
    message_type = forms.ChoiceField(
        choices=MESSAGE_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
        })
    )
    class_section = forms.ModelChoiceField(
        queryset=ClassSection.objects.all(),
        required=False,
        empty_label="All Classes",
        widget=forms.Select(attrs={
            'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
        })
    )
    message_content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500',
            'rows': 4,
            'placeholder': 'Enter your message here...',
            'maxlength': '160'
        })
    )
    
    def clean_message_content(self):
        content = self.cleaned_data['message_content']
        if len(content) < 10:
            raise ValidationError("Message must be at least 10 characters long")
        return content

class MessagingConfigForm(forms.ModelForm):
    class Meta:
        model = MessagingConfig
        fields = ['provider', 'api_key', 'sender_id', 'is_active']
        widgets = {
            'provider': forms.Select(attrs={
                'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'api_key': forms.TextInput(attrs={
                'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500',
                'type': 'password'
            }),
            'sender_id': forms.TextInput(attrs={
                'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded focus:ring-2 focus:ring-blue-500'
            })
        }