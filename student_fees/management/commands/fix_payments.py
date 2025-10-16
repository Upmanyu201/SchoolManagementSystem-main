from django.core.management.base import BaseCommand
from student_fees.models import FeeDeposit
from decimal import Decimal

class Command(BaseCommand):
    help = 'Fix incorrect payment calculations where amount = (original - discount)'

    def handle(self, *args, **options):
        self.stdout.write("Starting Payment Calculation Fix...")
        
        deposits_with_discounts = FeeDeposit.objects.filter(
            discount__gt=0
        ).exclude(fees_type__isnull=True)
        
        self.stdout.write(f"Found {deposits_with_discounts.count()} deposits with discounts")
        
        fixed_count = 0
        
        for deposit in deposits_with_discounts:
            if deposit.fees_type:
                original_fee_amount = deposit.fees_type.amount
                current_amount = deposit.amount
                discount = deposit.discount
                
                correct_amount = original_fee_amount
                correct_paid = original_fee_amount - discount
                
                if (current_amount == correct_paid and 
                    current_amount != correct_amount):
                    
                    self.stdout.write(f"Fixing Receipt {deposit.receipt_no}")
                    self.stdout.write(f"  Before: Amount={current_amount}, Discount={discount}")
                    
                    deposit.amount = correct_amount
                    deposit.paid_amount = correct_paid
                    deposit.save()
                    
                    self.stdout.write(f"  After: Amount={correct_amount}, Paid={correct_paid}")
                    fixed_count += 1
        
        self.stdout.write(f"Successfully fixed {fixed_count} payment records!")