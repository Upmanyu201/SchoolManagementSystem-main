from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import UserModulePermission

User = get_user_model()

class AddUserForm(UserCreationForm):
    """Form for adding new users"""
    
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-400 focus:ring-0',
            'placeholder': 'Enter first name'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-400 focus:ring-0',
            'placeholder': 'Enter last name'
        })
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-400 focus:ring-0',
            'placeholder': 'Enter email address'
        })
    )
    
    mobile = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-400 focus:ring-0',
            'placeholder': 'Enter mobile number'
        })
    )
    
    role = forms.ChoiceField(
        choices=[
            ('', 'Select Role'),
            ('admin', 'Admin'),
            ('teacher', 'Teacher'),
            ('student', 'Student'),
        ],
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-400 focus:ring-0'
        })
    )
    
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-5 w-5 text-blue-600 rounded focus:ring-blue-500'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'mobile', 'role', 'password1', 'password2', 'is_active')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-400 focus:ring-0',
                'placeholder': 'Enter username'
            }),
            'password1': forms.PasswordInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-400 focus:ring-0',
                'placeholder': 'Enter password'
            }),
            'password2': forms.PasswordInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-400 focus:ring-0',
                'placeholder': 'Confirm password'
            }),
        }

class ModulePermissionForm(forms.ModelForm):
    """2025 Industry Standard: Dynamic module permission form"""
    
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(is_superuser=False, is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_user'
        }),
        empty_label="Select a user..."
    )
    
    class Meta:
        model = UserModulePermission
        fields = [
            # Academic modules (removed 'user' from fields to prevent validation)
            'students_view', 'students_edit',
            'teachers_view', 'teachers_edit', 
            'subjects_view', 'subjects_edit',
            # Financial modules
            'fees_view', 'fees_edit',
            'payments_view', 'payments_edit',
            'fines_view', 'fines_edit',
            # Academic tracking
            'attendance_view', 'attendance_edit',
            # Administrative
            'transport_view', 'transport_edit',
            'reports_view', 'reports_edit',
            'messaging_view', 'messaging_edit',
            'promotion_view', 'promotion_edit',
            # System
            'users_view', 'users_edit',
            'settings_view', 'settings_edit',
            'backup_view', 'backup_edit',
            'school_profile_view', 'school_profile_edit',
        ]
        
        widgets = {
            # Academic modules
            'students_view': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'students_edit': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'teachers_view': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'teachers_edit': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'subjects_view': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'subjects_edit': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            
            # Financial modules
            'fees_view': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'fees_edit': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'payments_view': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'payments_edit': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            
            # Academic tracking
            'attendance_view': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'attendance_edit': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'fines_view': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'fines_edit': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            
            # Administrative
            'transport_view': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'transport_edit': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'reports_view': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'reports_edit': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            
            # System
            'users_view': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'users_edit': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'settings_view': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'settings_edit': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            
            # Additional modules
            'messaging_view': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'messaging_edit': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'promotion_view': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'promotion_edit': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'backup_view': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'backup_edit': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'school_profile_view': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'school_profile_edit': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add icons and better labels
        self.fields['students_view'].label = "Students View"
        self.fields['students_edit'].label = "Students Edit"
        self.fields['teachers_view'].label = "Teachers View"
        self.fields['teachers_edit'].label = "Teachers Edit"
        self.fields['subjects_view'].label = "Subjects View"
        self.fields['subjects_edit'].label = "Subjects Edit"
        
        self.fields['fees_view'].label = "Fees View"
        self.fields['fees_edit'].label = "Fees Edit"
        self.fields['payments_view'].label = "Payments View"
        self.fields['payments_edit'].label = "Payments Edit"
        
        self.fields['attendance_view'].label = "Attendance View"
        self.fields['attendance_edit'].label = "Attendance Edit"
        
        self.fields['transport_view'].label = "Transport View"
        self.fields['transport_edit'].label = "Transport Edit"
        self.fields['reports_view'].label = "Reports View"
        self.fields['reports_edit'].label = "Reports Edit"
        
        self.fields['users_view'].label = "Users View"
        self.fields['users_edit'].label = "Users Edit"
        self.fields['settings_view'].label = "Settings View"
        self.fields['settings_edit'].label = "Settings Edit"
        
        self.fields['fines_view'].label = "Fines View"
        self.fields['fines_edit'].label = "Fines Edit"
        self.fields['messaging_view'].label = "Messaging View"
        self.fields['messaging_edit'].label = "Messaging Edit"
        self.fields['promotion_view'].label = "Promotion View"
        self.fields['promotion_edit'].label = "Promotion Edit"
        self.fields['backup_view'].label = "Backup View"
        self.fields['backup_edit'].label = "Backup Edit"
        self.fields['school_profile_view'].label = "School Profile View"
        self.fields['school_profile_edit'].label = "School Profile Edit"
    
    def clean(self):
        """Validate that edit permissions require view permissions"""
        cleaned_data = super().clean()
        
        modules = ['students', 'teachers', 'subjects', 'fees', 'payments', 
                  'fines', 'attendance', 'transport', 'reports', 'messaging', 
                  'promotion', 'users', 'settings', 'backup', 'school_profile']
        
        for module in modules:
            view_field = f"{module}_view"
            edit_field = f"{module}_edit"
            
            view_value = cleaned_data.get(view_field, False)
            edit_value = cleaned_data.get(edit_field, False)
            
            if edit_value and not view_value:
                error_msg = f"Edit permission requires view permission for {module.title()}"
                self.add_error(edit_field, error_msg)
        
        return cleaned_data
    
    def save(self, commit=True):
        """Create or update permissions using safe method"""
        user = self.cleaned_data['user']
        
        # Prepare permission data from all fields except user
        permission_data = {}
        for field_name in self.Meta.fields:
            permission_data[field_name] = self.cleaned_data.get(field_name, False)
        
        # Use the safe get_or_create method
        permission, created = UserModulePermission.get_or_create_for_user(
            user=user,
            **permission_data
        )
        
        return permission