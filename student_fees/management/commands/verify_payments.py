from django.core.management.base import BaseCommand
from student_fees.models import FeeDeposit

class Command(BaseCommand):
    help = 'Verify payment calculations are correct'

    def handle(self, *args, **options):
        self.stdout.write("Verifying Payment Calculations...")
        
        all_deposits = FeeDeposit.objects.exclude(fees_type__isnull=True)
        
        correct_count = 0
        wrong_count = 0
        
        for deposit in all_deposits:
            if deposit.fees_type:
                original = deposit.fees_type.amount
                amount = deposit.amount
                discount = deposit.discount
                paid = deposit.paid_amount
                
                expected_paid = original - discount
                
                is_correct = (amount == original and paid == expected_paid)
                
                if is_correct:
                    correct_count += 1
                else:
                    wrong_count += 1
                    self.stdout.write(f"WRONG: {deposit.receipt_no}")
                    self.stdout.write(f"  Original: {original}, Stored: {amount}, Discount: {discount}, Paid: {paid}")
                    self.stdout.write(f"  Should be: Amount={original}, Paid={expected_paid}")
        
        self.stdout.write(f"\nResults:")
        self.stdout.write(f"Correct: {correct_count}")
        self.stdout.write(f"Wrong: {wrong_count}")
        
        if wrong_count == 0:
            self.stdout.write("All payment calculations are correct!")