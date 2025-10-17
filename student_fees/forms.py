# student_fees/forms.py
from django import forms
from decimal import Decimal
from .models import FeeDeposit


class FeePaymentForm(forms.ModelForm):
    """Form for fee payment processing"""
    
    class Meta:
        model = FeeDeposit
        fields = [
            'amount', 'discount', 'payment_mode', 
            'transaction_no', 'payment_source', 'note'
        ]
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'discount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'payment_mode': forms.Select(attrs={'class': 'form-control'}),
            'transaction_no': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_source': forms.TextInput(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount < 0:
            raise forms.ValidationError("Amount must be greater than zero")
        return amount
    
    def clean_discount(self):
        discount = self.cleaned_data.get('discount', Decimal('0'))
        amount = self.cleaned_data.get('amount', Decimal('0'))
        
        if discount and discount < 0:
            raise forms.ValidationError("Discount cannot be negative")
        
        if discount and amount and discount > amount:
            raise forms.ValidationError("Discount cannot be greater than amount")
        
        return discount
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Calculate paid amount
        instance.paid_amount = instance.amount - (instance.discount or Decimal('0'))
        
        if commit:
            instance.save()
        return instance