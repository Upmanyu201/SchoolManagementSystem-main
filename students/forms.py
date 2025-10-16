from django import forms
from django.core.exceptions import ValidationError
from django.utils.html import escape
from .models import Student
from subjects.models import ClassSection
from core.security_utils import sanitize_input
import re
from django.utils import timezone 


class StudentForm(forms.ModelForm):
    """Optimized and secure student form with comprehensive validation"""
    
    class Meta:
        model = Student
        fields = [
            'admission_number', 'first_name', 'last_name', 'father_name', 
            'mother_name', 'date_of_birth', 'date_of_admission', 'aadhaar_number',
            'pen_number', 'class_section', 'gender', 'religion', 'caste_category',
            'address', 'mobile_number', 'email', 'blood_group', 'student_image',
            'aadhar_card', 'transfer_certificate', 'status',
            'transfer_certificate', 'status'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter first name',
                'maxlength': '50'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter last name',
                'maxlength': '50'
            }),
            'father_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Enter father's name",
                'maxlength': '100'
            }),
            'mother_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Enter mother's name",
                'maxlength': '100'
            }),
            'admission_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter admission number',
                'maxlength': '20'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'date_of_admission': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'aadhaar_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter 12-digit Aadhaar number',
                'maxlength': '14'
            }),
            'pen_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter PEN number',
                'maxlength': '11'
            }),
            'class_section': forms.Select(attrs={
                'class': 'form-control'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-control'
            }),
            'religion': forms.Select(attrs={
                'class': 'form-control'
            }),
            'caste_category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter complete address'
            }),
            'mobile_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter 10-digit mobile number',
                'maxlength': '10'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email address'
            }),
            'blood_group': forms.Select(attrs={
                'class': 'form-control'
            }),
            'student_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'aadhar_card': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'transfer_certificate': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Optimize class_section queryset
        self.fields['class_section'].queryset = ClassSection.objects.select_related().all()
        
        # Set required fields
        required_fields = [
            'admission_number', 'first_name', 'last_name', 'father_name',
            'mother_name', 'date_of_birth', 'date_of_admission', 'gender',
            'religion', 'caste_category', 'address', 'mobile_number', 'email',
            'blood_group'
        ]
        
        # Make file uploads optional for easier testing
        optional_files = ['aadhar_card', 'transfer_certificate', 'student_image']
        for field_name in optional_files:
            if field_name in self.fields:
                self.fields[field_name].required = False
        
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True
        
        # Hide status field for new students (will use model default 'ACTIVE')
        if not self.instance.pk:
            self.fields['status'].widget = forms.HiddenInput()
            self.fields['status'].initial = 'ACTIVE'
            self.fields['status'].required = False
            if 'date_of_admission' in self.fields and not self.initial.get('date_of_admission'):
                self.fields['date_of_admission'].initial = timezone.localdate()
            
            if 'blood_group' in self.fields and not self.initial.get('blood_group'):
                self.fields['blood_group'].initial = 'UNKN'
                
            if 'status' in self.fields and not self.initial.get('status'):
                self.fields['status'].initial = 'ACTIVE'
    def clean_admission_number(self):
        """Validate and sanitize admission number"""
        admission_number = self.cleaned_data.get('admission_number')
        if not admission_number:
            raise ValidationError("Admission number is required.")
        
        # Sanitize input
        admission_number = sanitize_input(admission_number.strip().upper())
        
        # Validate format (alphanumeric, 3-20 characters)
        if not re.match(r'^[A-Z0-9]{3,20}$', admission_number):
            raise ValidationError("Admission number must be 3-20 alphanumeric characters.")
        
        # Check uniqueness (exclude current instance for updates)
        existing = Student.objects.filter(admission_number=admission_number)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise ValidationError("This admission number is already taken. Please choose a different one.")
        
        return admission_number

    def clean_first_name(self):
        """Validate and sanitize first name"""
        first_name = self.cleaned_data.get('first_name')
        if not first_name:
            raise ValidationError("First name is required.")
        
        first_name = sanitize_input(first_name.strip().title())
        
        if len(first_name) < 2:
            raise ValidationError("First name must be at least 2 characters long.")
        
        if not re.match(r'^[a-zA-Z\s]+$', first_name):
            raise ValidationError("First name can only contain letters and spaces.")
        
        return first_name

    def clean_last_name(self):
        """Validate and sanitize last name"""
        last_name = self.cleaned_data.get('last_name')
        if not last_name:
            raise ValidationError("Last name is required.")
        
        last_name = sanitize_input(last_name.strip().title())
        
        if len(last_name) < 2:
            raise ValidationError("Last name must be at least 2 characters long.")
        
        if not re.match(r'^[a-zA-Z\s]+$', last_name):
            raise ValidationError("Last name can only contain letters and spaces.")
        
        return last_name

    def clean_father_name(self):
        """Validate and sanitize father's name"""
        father_name = self.cleaned_data.get('father_name')
        if not father_name:
            raise ValidationError("Father's name is required.")
        
        father_name = sanitize_input(father_name.strip().title())
        
        if len(father_name) < 2:
            raise ValidationError("Father's name must be at least 2 characters long.")
        
        return father_name

    def clean_mother_name(self):
        """Validate and sanitize mother's name"""
        mother_name = self.cleaned_data.get('mother_name')
        if not mother_name:
            raise ValidationError("Mother's name is required.")
        
        mother_name = sanitize_input(mother_name.strip().title())
        
        if len(mother_name) < 2:
            raise ValidationError("Mother's name must be at least 2 characters long.")
        
        return mother_name

    def clean_mobile_number(self):
        """Validate mobile number"""
        mobile = self.cleaned_data.get('mobile_number')
        if not mobile:
            raise ValidationError("Mobile number is required.")
        
        mobile = sanitize_input(mobile.strip())
        
        if not re.match(r'^[6-9]\d{9}$', mobile):
            raise ValidationError("Please enter a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9.")
        
        return mobile

    def clean_email(self):
        """Validate and sanitize email"""
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError("Email is required.")
        
        email = sanitize_input(email.strip().lower())
        
        # Check uniqueness (exclude current instance for updates)
        existing = Student.objects.filter(email=email)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise ValidationError("This email is already registered. Please use a different email.")
        
        return email

    def clean_aadhaar_number(self):
        """Validate Aadhaar number if provided"""
        aadhaar = self.cleaned_data.get('aadhaar_number')
        if not aadhaar:
            return aadhaar
        
        aadhaar = sanitize_input(aadhaar.strip().replace(' ', '').replace('-', ''))
        
        if not re.match(r'^\d{12}$', aadhaar):
            raise ValidationError("Aadhaar number must be exactly 12 digits.")
        
        # Basic Aadhaar validation (Verhoeff algorithm would be ideal)
        if aadhaar == '000000000000' or len(set(aadhaar)) == 1:
            raise ValidationError("Please enter a valid Aadhaar number.")
        
        return aadhaar

    def clean_address(self):
        """Validate and sanitize address"""
        address = self.cleaned_data.get('address')
        if not address:
            raise ValidationError("Address is required.")
        
        address = sanitize_input(address.strip())
        
        if len(address) < 10:
            raise ValidationError("Please enter a complete address (at least 10 characters).")
        
        return address

    def clean_student_image(self):
        """Validate student image"""
        image = self.cleaned_data.get('student_image')
        if image:
            # Check file size (max 5MB)
            if image.size > 5 * 1024 * 1024:
                raise ValidationError("Image file size must be less than 5MB.")
            
            # Check file type
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png']
            if hasattr(image, 'content_type') and image.content_type not in allowed_types:
                raise ValidationError("Only JPEG and PNG images are allowed.")
        
        return image

    def clean_aadhar_card(self):
        """Validate Aadhaar card document"""
        document = self.cleaned_data.get('aadhar_card')
        if document:
            # Check file size (max 10MB)
            if document.size > 10 * 1024 * 1024:
                raise ValidationError("Document file size must be less than 10MB.")
            
            # Check file type
            allowed_types = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png']
            if hasattr(document, 'content_type') and document.content_type not in allowed_types:
                raise ValidationError("Only PDF, JPEG and PNG files are allowed for Aadhaar card.")
        
        return document

    def clean_transfer_certificate(self):
        """Validate transfer certificate document"""
        document = self.cleaned_data.get('transfer_certificate')
        if document:
            # Check file size (max 10MB)
            if document.size > 10 * 1024 * 1024:
                raise ValidationError("Document file size must be less than 10MB.")
            
            # Check file type
            allowed_types = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png']
            if hasattr(document, 'content_type') and document.content_type not in allowed_types:
                raise ValidationError("Only PDF, JPEG and PNG files are allowed for transfer certificate.")
        
        return document

    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()
        
        # Ensure new students always get ACTIVE status
        if not self.instance.pk and not cleaned_data.get('status'):
            cleaned_data['status'] = 'ACTIVE'
        
        date_of_birth = cleaned_data.get('date_of_birth')
        date_of_admission = cleaned_data.get('date_of_admission')
        
        if date_of_birth and date_of_admission:
            # Check if admission date is after birth date
            if date_of_admission <= date_of_birth:
                raise ValidationError("Date of admission must be after date of birth.")
            
            # Check minimum age (assuming 3 years minimum)
            age_at_admission = (date_of_admission - date_of_birth).days / 365.25
            if age_at_admission < 3:
                raise ValidationError("Student must be at least 3 years old at the time of admission.")
            
            if age_at_admission > 25:
                raise ValidationError("Please verify the dates - student age seems unusually high.")
        
        return cleaned_data