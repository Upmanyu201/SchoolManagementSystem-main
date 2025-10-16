from django import forms
from .models import Fine, FineType, FineStudent, FineAuditLog, FineTemplate
from students.models import Student
from subjects.models import ClassSection
from fees.models import FeesGroup, FeesType
from django.core.exceptions import ValidationError
from django.contrib import messages
import logging

logger = logging.getLogger("myapp")

class FineForm(forms.ModelForm):
    target_scope = forms.ChoiceField(choices=[('Individual', 'Individual'), ('Class', 'Class'), ('All', 'All Students')])
    class_section = forms.ModelChoiceField(
        queryset=ClassSection.objects.all(), 
        required=False, 
        label="Select Class Section",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'data-placeholder': 'Choose a class to apply fine...'
        })
    )
    fine_template = forms.ModelChoiceField(
        queryset=FineTemplate.objects.all(),
        required=False,
        label="Select Fine Template",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    fees_group = forms.ModelChoiceField(
        queryset=FeesGroup.objects.all(),
        required=False,
        label="Fees Group (Apply to all fee types in group)",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    fees_types = forms.ModelMultipleChoiceField(
        queryset=FeesType.objects.all(),
        required=False,
        label="Multiple Fee Types",
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'fee-type-checkbox'})
    )
    delay_days = forms.IntegerField(
        initial=0,
        min_value=0,
        required=False,
        label="Delay Days",
        help_text="Days after due date when fine will be applied",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'})
    )

    class Meta:
        model = Fine
        fields = ['fine_template', 'fine_type', 'fees_group', 'fees_types', 'amount', 'dynamic_amount_percent', 'reason', 'due_date', 'delay_days', 'target_scope', 'class_section']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'amount': forms.NumberInput(attrs={
                'step': '0.01', 
                'min': '0.01',
                'placeholder': 'Fixed Amount (₹)'
            }),
            'dynamic_amount_percent': forms.NumberInput(attrs={
                'step': '0.01', 
                'min': '0.01',
                'max': '100',
                'placeholder': 'e.g., 0.5 for 0.5%'
            }),
            'reason': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Make amount field not required (will be validated in clean method)
        self.fields['amount'].required = False
        
        # Set field requirements based on target_scope
        if 'target_scope' in self.data:
            target_scope = self.data.get('target_scope')
            self.fields['class_section'].required = (target_scope == 'Class')
            logger.info(f"Form init - target_scope: {target_scope}, class_section required: {self.fields['class_section'].required}")
        else:
            # Default: class_section not required
            self.fields['class_section'].required = False
            
        # Set querysets for related fields
        try:
            self.fields['fine_type'].queryset = FineType.objects.filter(is_active=True).order_by('name')
            self.fields['fine_type'].empty_label = "Select Fine Type"
        except:
            self.fields['fine_type'].queryset = FineType.objects.all().order_by('name')
            self.fields['fine_type'].empty_label = "Select Fine Type"
        
        try:
            self.fields['fees_group'].queryset = FeesGroup.objects.all().order_by('fee_group')
            self.fields['fees_group'].empty_label = "Select Fees Group"
        except:
            self.fields['fees_group'].queryset = FeesGroup.objects.none()
            self.fields['fees_group'].empty_label = "No Fees Groups Available"
        
        try:
            self.fields['fees_types'].queryset = FeesType.objects.select_related('fee_group').order_by('fee_group__group_type', 'amount_type')
        except:
            self.fields['fees_types'].queryset = FeesType.objects.none()
        
        # Add CSS classes for better styling
        self.fields['class_section'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-red-400 focus:ring-0 transition-all duration-300',
            'data-placeholder': 'Choose a class section...'
        })
        self.fields['target_scope'].widget.attrs.update({
            'class': 'form-select'
        })
        self.fields['fine_type'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-red-400 focus:ring-0 transition-all duration-300'
        })
        self.fields['fees_group'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-red-400 focus:ring-0 transition-all duration-300'
        })
        self.fields['fees_types'].widget.attrs.update({
            'class': 'fee-type-checkbox'
        })

    def clean(self):
        cleaned_data = super().clean()
        target_scope = cleaned_data.get('target_scope')
        amount = cleaned_data.get('amount')
        dynamic_amount_percent = cleaned_data.get('dynamic_amount_percent')
        fine_template = cleaned_data.get('fine_template')
        class_section = cleaned_data.get('class_section')

        logger.info(f"Form validation - Target Scope: {target_scope}, Amount: {amount}, Dynamic Amount: {dynamic_amount_percent}")

        # Apply template values if selected
        if fine_template:
            cleaned_data['fine_type'] = fine_template.fine_type
            cleaned_data['amount'] = cleaned_data['amount'] or fine_template.amount
            cleaned_data['dynamic_amount_percent'] = cleaned_data['dynamic_amount_percent'] or fine_template.dynamic_amount_percent
            cleaned_data['reason'] = cleaned_data['reason'] or fine_template.reason

        fees_group = cleaned_data.get('fees_group')
        fees_types = cleaned_data.get('fees_types')

        # Allow custom fines: fee group/type not required if amount is set
        has_amount = amount is not None and float(amount or 0) > 0
        has_percentage = dynamic_amount_percent is not None and float(dynamic_amount_percent or 0) > 0

        if has_amount and has_percentage:
            raise ValidationError("Please specify either a fixed amount OR a percentage, not both.")

        if not has_amount and not has_percentage:
            raise ValidationError("Please specify either a fixed amount or a percentage.")

        # If percentage-based, require fee group/type
        if has_percentage and not fees_group and not fees_types:
            raise ValidationError("Please select fee types or a fee group when using percentage-based fine calculation.")

        # Validate percentage range
        if dynamic_amount_percent is not None:
            try:
                percent_value = float(dynamic_amount_percent)
                if percent_value <= 0 or percent_value > 100:
                    raise ValidationError("Percentage must be between 0.01% and 100%.")
            except (ValueError, TypeError):
                raise ValidationError("Please enter a valid percentage value.")

        # Validate fixed amount
        if amount is not None:
            try:
                amount_value = float(amount)
                if amount_value <= 0:
                    raise ValidationError("Amount must be greater than 0.")
            except (ValueError, TypeError):
                raise ValidationError("Please enter a valid amount.")

        # Set default amount for percentage-based fines (will be calculated during application)
        if has_percentage and not amount:
            cleaned_data['amount'] = 1.00  # Placeholder, will be calculated per student

        # Validate class section for Class scope
        if target_scope == 'Class' and not class_section:
            raise ValidationError({"class_section": "Class Section is required for Class scope."})

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        target_scope = self.cleaned_data['target_scope']
        user = self.initial.get('user', None)
        
        logger.info(f"Form save method - target_scope: {target_scope}, user: {user}")
        
        instance.target_scope = target_scope
        if user:
            instance.created_by = user

        if commit:
            instance.save()
            
            # Set up many-to-many relationships
            fees_group = self.cleaned_data.get('fees_group')
            fees_types = self.cleaned_data.get('fees_types')
            
            if fees_group:
                instance.fees_group = fees_group
                # Add all fee types from the group
                from fees.models import FeesType
                group_fee_types = FeesType.objects.filter(fee_group=fees_group)
                instance.fees_types.set(group_fee_types)
                logger.info(f"Set {group_fee_types.count()} fee types from group {fees_group}")
            elif fees_types:
                instance.fees_types.set(fees_types)
                logger.info(f"Set {fees_types.count()} individual fee types")
            
            # Note: Student assignment will be handled in the view after form save
            # This allows for proper handling of selected students in Individual scope
            
            logger.info(f"Form save method - successfully saved fine ID: {instance.id}")
        else:
            logger.info("Form save method - commit=False, not saving to DB yet")

        return instance

class FineTypeForm(forms.ModelForm):
    class Meta:
        model = FineType
        fields = ['name', 'category', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-red-400 focus:ring-0 transition-all duration-300',
                'placeholder': 'e.g., Late Fee, Library Fine'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-red-400 focus:ring-0 transition-all duration-300'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-red-400 focus:ring-0 transition-all duration-300',
                'rows': 4,
                'placeholder': 'Describe when this fine type should be applied...'
            })
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise ValidationError("Fine type name is required.")
        if len(name) < 3:
            raise ValidationError("Fine type name must be at least 3 characters long.")
        if len(name) > 100:
            raise ValidationError("Fine type name cannot exceed 100 characters.")
        
        # Check for duplicate names (case-insensitive)
        if FineType.objects.filter(name__iexact=name).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise ValidationError("A fine type with this name already exists.")
        
        return name

class FineWaiverForm(forms.Form):
    """Form to waive fines for students"""
    fine_student_ids = forms.CharField(widget=forms.HiddenInput())
    waiver_reason = forms.CharField(
        max_length=500,
        required=True,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Enter reason for waiving this fine...',
            'class': 'form-control'
        })
    )
    
    def clean_fine_student_ids(self):
        ids_str = self.cleaned_data.get('fine_student_ids', '')
        if not ids_str:
            raise ValidationError("No fine students selected.")
        
        try:
            ids = [int(id_str.strip()) for id_str in ids_str.split(',') if id_str.strip()]
            if not ids:
                raise ValidationError("No valid fine student IDs provided.")
            return ids
        except ValueError:
            raise ValidationError("Invalid fine student IDs format.")
    
    def waive_fines(self, user):
        """Waive selected fines"""
        from django.utils import timezone
        
        fine_student_ids = self.cleaned_data['fine_student_ids']
        waiver_reason = self.cleaned_data['waiver_reason']
        
        waived_count = 0
        for fs_id in fine_student_ids:
            try:
                fine_student = FineStudent.objects.get(id=fs_id)
                if not fine_student.is_paid and not fine_student.is_waived:
                    fine_student.is_waived = True
                    fine_student.waived_by = user
                    fine_student.waived_date = timezone.now()
                    fine_student.save()
                    
                    # Log the waiver
                    FineAuditLog.objects.create(
                        fine=fine_student.fine,
                        action='WAIVED',
                        user=user,
                        details={
                            'student_id': fine_student.student.id,
                            'reason': waiver_reason,
                            'amount': str(fine_student.fine.amount)
                        }
                    )
                    waived_count += 1
            except FineStudent.DoesNotExist:
                continue
        
        return waived_count

class FineVerificationForm(forms.Form):
    """Form to verify and fix fine applications"""
    fine_id = forms.IntegerField(widget=forms.HiddenInput())
    
    def clean_fine_id(self):
        fine_id = self.cleaned_data.get('fine_id')
        if fine_id:
            try:
                Fine.objects.get(id=fine_id)
            except Fine.DoesNotExist:
                raise ValidationError("Fine not found.")
        return fine_id
    
    def verify_fine(self):
        """Verify fine application using centralized service"""
        from core.fee_management.services import fee_service
        
        fine_id = self.cleaned_data['fine_id']
        return fee_service.verify_fine_application(fine_id)
    
    def fix_fine(self):
        """Fix incorrect fine application"""
        from core.fee_management.services import fee_service
        
        fine_id = self.cleaned_data['fine_id']
        return fee_service.fix_incorrect_fine_application(fine_id)