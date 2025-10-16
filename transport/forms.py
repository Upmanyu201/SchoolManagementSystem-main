from django import forms
from .models import Route, Stoppage, TransportAssignment
from students.models import Student
from django.core.exceptions import ValidationError

class RouteForm(forms.ModelForm):
    class Meta:
        model = Route
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-400 focus:ring-0 transition-all duration-300 bg-white',
                'placeholder': 'Enter route name (e.g., Route A, Main Road)',
                'maxlength': '100',
                'required': True,
                'autocomplete': 'off'
            }),
        }
        
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            if len(name) < 2:
                raise ValidationError("Route name must be at least 2 characters long.")
            # Check for duplicate names (excluding current instance if editing)
            qs = Route.objects.filter(name__iexact=name)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(f"A route with the name '{name}' already exists. Please choose a different name.")
        return name

class StoppageForm(forms.ModelForm):
    class Meta:
        model = Stoppage
        fields = ['route', 'name']
        widgets = {
            'route': forms.Select(attrs={
                'class': 'form-select w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-400 focus:ring-0 transition-all duration-300 bg-white',
                'required': True
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-input w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-400 focus:ring-0 transition-all duration-300 bg-white',
                'placeholder': 'Enter stoppage name (e.g., Main Gate, Bus Stand)',
                'maxlength': '100',
                'required': True,
                'autocomplete': 'off'
            }),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['route'].queryset = Route.objects.all().order_by('name')
        self.fields['route'].empty_label = "Select a route"
        
    def clean_name(self):
        name = self.cleaned_data.get('name')
        route = self.cleaned_data.get('route')
        
        if name:
            name = name.strip()
            if len(name) < 2:
                raise ValidationError("Stoppage name must be at least 2 characters long.")
                
            # Check for duplicate names within the same route
            if route:
                qs = Stoppage.objects.filter(route=route, name__iexact=name)
                if self.instance.pk:
                    qs = qs.exclude(pk=self.instance.pk)
                if qs.exists():
                    raise ValidationError(f"A stoppage named '{name}' already exists on route '{route.name}'. Please choose a different name.")
        return name

class TransportAssignmentForm(forms.ModelForm):
    student = forms.ModelChoiceField(
        queryset=Student.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-select w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-400 focus:ring-0 transition-all duration-300 bg-white',
            'required': True
        }),
        empty_label="Select a student"
    )

    class Meta:
        model = TransportAssignment
        fields = ['student', 'stoppage']
        widgets = {
            'stoppage': forms.Select(attrs={
                'class': 'form-select w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-400 focus:ring-0 transition-all duration-300 bg-white',
                'required': True
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['stoppage'].queryset = Stoppage.objects.select_related('route').all().order_by('route__name', 'name')
        self.fields['stoppage'].empty_label = "Select a stoppage"
        
        # Show unassigned students first, then all students
        assigned_student_ids = TransportAssignment.objects.values_list('student_id', flat=True)
        unassigned_students = Student.objects.exclude(id__in=assigned_student_ids).order_by('first_name', 'last_name')
        all_students = Student.objects.all().order_by('first_name', 'last_name')
        
        # If editing, include the current student
        if self.instance.pk and self.instance.student:
            self.fields['student'].queryset = all_students
        else:
            self.fields['student'].queryset = unassigned_students

    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get('student')
        stoppage = cleaned_data.get('stoppage')

        # Ensure student is not already assigned (ignore current instance in case of edit)
        if student:
            qs = TransportAssignment.objects.filter(student=student)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                existing_assignment = qs.first()
                raise ValidationError(f"{student.get_full_display_name()} is already assigned to {existing_assignment.stoppage.name} on route {existing_assignment.route.name}. Please choose a different student or remove the existing assignment first.")

        return cleaned_data       






