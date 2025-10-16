from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from datetime import datetime
from students.models import Student
from messaging.fee_messaging import FeeMessagingService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test payment confirmation SMS to both admin and parents'

    def add_arguments(self, parser):
        parser.add_argument(
            '--student-id',
            type=int,
            help='Specific student ID to test (optional)',
        )
        parser.add_argument(
            '--amount',
            type=float,
            default=1000.00,
            help='Test payment amount (default: 1000.00)',
        )

    def handle(self, *args, **options):
        self.stdout.write("🚀 Testing Payment Messaging System")
        self.stdout.write("=" * 50)
        
        # Initialize messaging service
        messaging_service = FeeMessagingService()
        
        # Get test student
        if options['student_id']:
            try:
                student = Student.objects.get(id=options['student_id'])
            except Student.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Student with ID {options['student_id']} not found"))
                return
        else:
            student = Student.objects.first()
            if not student:
                self.stdout.write(self.style.ERROR("No students found in database"))
                return
        
        self.stdout.write(f"👤 Testing with student: {student.get_full_name()}")
        self.stdout.write(f"📞 Student mobile: {student.mobile_number or 'Not provided'}")
        
        # Test admin phone
        admin_phone = messaging_service.get_admin_phone()
        self.stdout.write(f"👨💼 Admin phone: {admin_phone}")
        
        # Test payment confirmation SMS
        self.stdout.write("\n📱 Testing Payment Confirmation SMS...")
        
        test_amount = Decimal(str(options['amount']))
        receipt_no = f"TEST{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        try:
            result = messaging_service.send_payment_confirmation_sms(
                student=student,
                paid_amount=test_amount,
                payment_date=datetime.now().date(),
                receipt_no=receipt_no,
                payment_mode='Cash',
                fee_types=['Academic - Monthly Fee', 'Test Payment'],
                fine_amount=None,
                remaining_amount=Decimal('0.00')
            )
            
            if result:
                self.stdout.write(self.style.SUCCESS("✅ Payment confirmation SMS test PASSED"))
                self.stdout.write("   📤 Parent SMS: Attempted")
                self.stdout.write("   📤 Admin SMS: Attempted")
            else:
                self.stdout.write(self.style.ERROR("❌ Payment confirmation SMS test FAILED"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Test failed with error: {e}"))
            logger.exception("Payment SMS test error")
        
        # Test individual components
        self.test_individual_messages(messaging_service, student, test_amount)
        
        # Summary
        self.stdout.write("\n📊 Test Summary:")
        self.stdout.write("=" * 30)
        self.stdout.write("✅ Payment messaging system tested")
        self.stdout.write("📱 Admin notifications should be successful (verified number)")
        self.stdout.write("📱 Parent notifications may fail if phone unverified")
        self.stdout.write("\n💡 Check Django logs for detailed SMS sending information")
    
    def test_individual_messages(self, messaging_service, student, amount):
        """Test individual message components"""
        self.stdout.write("\n🔍 Testing Individual Message Components...")
        
        # Create sample messages
        parent_message = (
            f"🎓 PAYMENT RECEIVED\n"
            f"💰 Amount: ₹{amount}\n"
            f"👤 Student: {student.get_full_name()}\n"
            f"🆔 Admission: {student.admission_number}\n"
            f"📚 Class: {student.student_class.display_name if student.student_class else 'N/A'}\n"
            f"📅 Date: {datetime.now().strftime('%d-%m-%Y %I:%M %p')}\n"
            f"💳 Mode: Cash\n"
            f"🧾 Receipt: #TEST123\n"
            f"📋 Fees: Academic - Monthly Fee\n"
            f"✅ Account: Fully Paid\n"
            f"🏫 {messaging_service.school_name}\nThank you for your payment!"
        )
        
        admin_message = (
            f"💼 PAYMENT ALERT\n"
            f"👤 Student: {student.get_full_name()}\n"
            f"🆔 Admission: {student.admission_number}\n"
            f"📚 Class: {student.student_class.display_name if student.student_class else 'N/A'}\n"
            f"💰 Amount: ₹{amount}\n"
            f"💳 Mode: Cash\n"
            f"📋 Type: Academic - Monthly Fee\n"
            f"📅 Date: {datetime.now().strftime('%d-%m-%Y %I:%M %p')}\n"
            f"🧾 Receipt: #TEST123\n"
            f"⏳ Remaining: ₹0.00\n"
            f"🏫 {messaging_service.school_name}"
        )
        
        self.stdout.write("📝 Parent Message Preview:")
        self.stdout.write("-" * 30)
        preview = parent_message[:200] + "..." if len(parent_message) > 200 else parent_message
        self.stdout.write(preview)
        
        self.stdout.write("\n📝 Admin Message Preview:")
        self.stdout.write("-" * 30)
        preview = admin_message[:200] + "..." if len(admin_message) > 200 else admin_message
        self.stdout.write(preview)
        
        # Test sending to admin (verified number)
        self.stdout.write("\n📤 Testing Admin SMS...")
        admin_phone = messaging_service.get_admin_phone()
        
        try:
            result = messaging_service.messaging_service.send_sms(admin_phone, admin_message)
            
            if result['success']:
                self.stdout.write(self.style.SUCCESS(f"✅ Admin SMS sent successfully - ID: {result.get('sid')}"))
            else:
                self.stdout.write(self.style.WARNING(f"❌ Admin SMS failed: {result.get('error')}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Admin SMS error: {e}"))
        
        # Test sending to parent (may fail if unverified)
        if student.mobile_number:
            self.stdout.write("\n📤 Testing Parent SMS...")
            try:
                result = messaging_service.messaging_service.send_sms(student.mobile_number, parent_message)
                
                if result['success']:
                    self.stdout.write(self.style.SUCCESS(f"✅ Parent SMS sent successfully - ID: {result.get('sid')}"))
                else:
                    self.stdout.write(self.style.WARNING(f"⚠️ Parent SMS failed (expected if unverified): {result.get('error')}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Parent SMS error: {e}"))
        else:
            self.stdout.write("⚠️ Student has no mobile number - Parent SMS skipped")