# fees/forms.py
from django import forms
from .models import FeesGroup, FeesType
from django.core.exceptions import ValidationError

# Safe imports for related models
try:
    from subjects.models import ClassSection
except ImportError:
    ClassSection = None

try:
    from transport.models import Stoppage
except ImportError:
    Stoppage = None



class FeesGroupForm(forms.ModelForm):
    class Meta:
        model = FeesGroup
        fields = ['fee_group', 'group_type', 'fee_type', 'related_class_section', 'related_stoppage']
        widgets = {
            'fee_group': forms.Select(attrs={
                'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500',
                'id': 'feeGroup'
            }),
            'group_type': forms.Select(attrs={
                'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500',
                'id': 'groupType'
            }),
            'fee_type': forms.Select(attrs={
                'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500',
                'id': 'feeType'
            }),
            'related_class_section': forms.Select(attrs={
                'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'related_stoppage': forms.Select(attrs={
                'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set empty labels for better UX
        self.fields['fee_group'].empty_label = "-- Select Fee Group --"
        self.fields['group_type'].empty_label = "-- Select Group Type --"
        self.fields['fee_type'].empty_label = "-- Select Fee Type --"
        self.fields['related_class_section'].empty_label = "-- Select Class Section --"
        self.fields['related_stoppage'].empty_label = "-- Select Stoppage --"
        
        # Populate related fields safely
        if ClassSection:
            self.fields['related_class_section'].queryset = ClassSection.objects.all()
        else:
            self.fields['related_class_section'].queryset = self.fields['related_class_section'].queryset.none()
            
        if Stoppage:
            self.fields['related_stoppage'].queryset = Stoppage.objects.all()
        else:
            self.fields['related_stoppage'].queryset = self.fields['related_stoppage'].queryset.none()

    def clean(self):
        cleaned_data = super().clean()
        fee_group = cleaned_data.get('fee_group')
        group_type = cleaned_data.get('group_type')
        fee_type = cleaned_data.get('fee_type')
        
        # Check for uniqueness with user-friendly message
        if FeesGroup.objects.filter(
            fee_group=fee_group,
            group_type=group_type,
            fee_type=fee_type
        ).exclude(id=self.instance.id).exists():
            raise ValidationError(
                f"This fee group combination already exists: '{fee_group} - {group_type} - {fee_type}'. "
                f"Please try a different Fee Type (like 'General' instead of '{fee_type}') or use the existing group."
            )
        
        return cleaned_data
        
        
class DynamicFeesTypeForm(forms.ModelForm):
    # User input for amount type
    amount_type = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-pink-400 focus:ring-0 transition-all duration-300',
            'placeholder': 'e.g., Jan25, Mar25, Quarterly',
            'id': 'amount_type_input'
        }),
        help_text="Enter amount type (e.g., Jan25, Feb25, Quarterly, Year2025)"
    )
    
    # Dynamic context fields
    selected_months = forms.MultipleChoiceField(
        choices=[
            ('January', 'January'), ('February', 'February'), ('March', 'March'),
            ('April', 'April'), ('May', 'May'), ('June', 'June'),
            ('July', 'July'), ('August', 'August'), ('September', 'September'),
            ('October', 'October'), ('November', 'November'), ('December', 'December'),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    selected_classes = forms.MultipleChoiceField(
        choices=[],
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    selected_stoppages = forms.MultipleChoiceField(
        choices=[],
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    custom_fee_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter fee name (e.g., Admission Fee)'
        })
    )
    
    class Meta:
        model = FeesType
        fields = ['fee_group', 'amount_type', 'amount']
        widgets = {
            'fee_group': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-pink-400 focus:ring-0 transition-all duration-300',
                'id': 'fee_group',
                'onchange': 'updateGroupDetails(this.value)'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-pink-400 focus:ring-0 transition-all duration-300',
                'placeholder': 'Enter Amount',
                'step': '0.01',
                'id': 'amount_input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Dynamic choices are already imported at module level
        
        # Class choices
        if ClassSection:
            try:
                class_choices = [(cs.display_name, cs.display_name) 
                                for cs in ClassSection.objects.all().order_by('class_name', 'section_name')]
                self.fields['selected_classes'].choices = class_choices
            except:
                self.fields['selected_classes'].choices = []
        else:
            self.fields['selected_classes'].choices = []
        
        # Stoppage choices
        if Stoppage:
            try:
                stoppage_choices = [(s.id, s.name) 
                                   for s in Stoppage.objects.all().order_by('name')]
                self.fields['selected_stoppages'].choices = stoppage_choices
            except:
                self.fields['selected_stoppages'].choices = []
        else:
            self.fields['selected_stoppages'].choices = []
        
        # Fee group queryset
        self.fields['fee_group'].queryset = FeesGroup.objects.all()
        self.fields['fee_group'].empty_label = "-- Select Fee Group --"
    
    def clean(self):
        cleaned_data = super().clean()
        fee_group = cleaned_data.get('fee_group')
        amount_type = cleaned_data.get('amount_type')
        
        if not fee_group:
            raise ValidationError("Please select a fee group.")
        
        if not amount_type or not amount_type.strip():
            raise ValidationError("Please enter an amount type.")
        
        # Determine context type based on fee group
        fee_group_name = fee_group.fee_group.lower()
        fee_type = fee_group.fee_type.lower()
        
        if 'monthly' in fee_group_name:
            context_type = 'monthly'
            selected_months = cleaned_data.get('selected_months', [])
            if not selected_months:
                raise ValidationError("Please select at least one month for monthly fees.")
            cleaned_data['context_data'] = {'months': selected_months}
        
        elif 'class based' in fee_type:
            context_type = 'class_based'
            selected_classes = cleaned_data.get('selected_classes', [])
            if not selected_classes:
                raise ValidationError("Please select at least one class for class-based fees.")
            cleaned_data['context_data'] = {'classes': selected_classes}
        
        elif 'stoppage based' in fee_type:
            context_type = 'stoppage_based'
            selected_stoppages = cleaned_data.get('selected_stoppages', [])
            if not selected_stoppages:
                raise ValidationError("Please select at least one stoppage for stoppage-based fees.")
            
            # Convert stoppage IDs to names for context_data
            if Stoppage:
                try:
                    stoppage_names = [Stoppage.objects.get(id=int(s_id)).name for s_id in selected_stoppages]
                    cleaned_data['context_data'] = {'stoppages': stoppage_names}
                except (Stoppage.DoesNotExist, ValueError):
                    raise ValidationError("Invalid stoppage selection.")
            else:
                cleaned_data['context_data'] = {'stoppages': selected_stoppages}
        
        elif 'general' in fee_type:
            context_type = 'general'
            custom_name = cleaned_data.get('custom_fee_name', '').strip()
            if not custom_name:
                raise ValidationError("Please enter a fee name for general fees.")
            cleaned_data['context_data'] = {'custom_name': custom_name}
        
        else:
            context_type = 'general'
            cleaned_data['context_data'] = {}
        
        cleaned_data['context_type'] = context_type
        return cleaned_data

# Keep old form for backward compatibility
class FeesTypeForm(DynamicFeesTypeForm):
    pass

    # class FeesPaymentForm(forms.ModelForm):
    #     class Meta:
    #         model = FeesPayment
    #         fields = ['student', 'fee_type', 'paid_amount', 'mode_of_payment', 'transaction_number', 'remarks']
