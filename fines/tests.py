
from django.test import TestCase
from django.contrib.auth import get_user_model
from datetime import date, timedelta
from .models import FineType, Fine, FineStudent, FineAuditLog
from students.models import Student
from subjects.models import ClassSection
from fees.models import FeesType, FeesGroup
from . import utils as fines_utils

class FineManagementTests(TestCase):
	def setUp(self):
		User = get_user_model()
		self.admin = User.objects.create(username='admin', is_superuser=True)
		self.class_section = ClassSection.objects.create(class_name='10', section_name='A')
		self.student = Student.objects.create(
			first_name='John',
			last_name='Doe',
			admission_number='ADM001',
			class_section=self.class_section,
			date_of_birth='2005-01-01',
			date_of_admission='2020-04-01'
		)
		self.fee_group = FeesGroup.objects.create(fee_group='Monthly')
		self.fee_type = FeesType.objects.create(
			fee_group=self.fee_group,
			amount=100,
			amount_type='Jan25',
			context_type='general'
		)
		self.fine_type = FineType.objects.create(name='Late Fee', category='Late Fee', description='Late payment')

	def test_apply_fine_after_grace_period(self):
		due = date.today() - timedelta(days=10)
		fine = Fine.objects.create(
			class_section=self.class_section,
			fine_type=self.fine_type,
			fees_group=self.fee_group,
			amount=50,
			reason='Late payment',
			due_date=due,
			delay_days=5,
			target_scope='Class',
			created_by=self.admin
		)
		result = fines_utils.apply_fine_to_eligible_students(fine)
		self.assertTrue(result['eligible_count'] > 0)
		self.assertEqual(FineStudent.objects.filter(fine=fine).count(), result['eligible_count'])

	def test_percentage_based_fine(self):
		due = date.today() - timedelta(days=10)
		fine = Fine.objects.create(
			class_section=self.class_section,
			fine_type=self.fine_type,
			fees_group=self.fee_group,
			amount=0,
			dynamic_amount_percent=10,
			reason='Late payment',
			due_date=due,
			delay_days=5,
			target_scope='Class',
			created_by=self.admin
		)
		result = fines_utils.apply_fine_to_eligible_students(fine)
		fs = FineStudent.objects.filter(fine=fine).first()
		self.assertTrue(fs.calculated_amount > 0)

	def test_fixed_amount_fine(self):
		due = date.today() - timedelta(days=10)
		fine = Fine.objects.create(
			class_section=self.class_section,
			fine_type=self.fine_type,
			amount=25,
			reason='Fixed fine',
			due_date=due,
			delay_days=5,
			target_scope='Class',
			created_by=self.admin
		)
		result = fines_utils.apply_fine_to_eligible_students(fine)
		fs = FineStudent.objects.filter(fine=fine).first()
		self.assertEqual(fs.calculated_amount, 25)

	def test_apply_fine_to_all_students(self):
		student2 = Student.objects.create(
			first_name='Jane',
			last_name='Smith',
			admission_number='ADM002',
			class_section=self.class_section,
			date_of_birth='2005-02-02',
			date_of_admission='2020-04-01'
		)
		due = date.today() - timedelta(days=10)
		fine = Fine.objects.create(
			fine_type=self.fine_type,
			amount=10,
			reason='School-wide fine',
			due_date=due,
			delay_days=5,
			target_scope='All',
			created_by=self.admin
		)
		result = fines_utils.apply_fine_to_eligible_students(fine)
		self.assertEqual(FineStudent.objects.filter(fine=fine).count(), 2)

	def test_waive_fine_and_audit(self):
		due = date.today() - timedelta(days=10)
		fine = Fine.objects.create(
			class_section=self.class_section,
			fine_type=self.fine_type,
			amount=20,
			reason='Waivable fine',
			due_date=due,
			delay_days=5,
			target_scope='Class',
			created_by=self.admin
		)
		fines_utils.apply_fine_to_eligible_students(fine)
		fs = FineStudent.objects.filter(fine=fine).first()
		result = fines_utils.waive_fine_students([fs.id], 'Valid reason', self.admin)
		self.assertTrue(result['success'])
		audit = FineAuditLog.objects.filter(fine=fine, action='WAIVED').first()
		self.assertIsNotNone(audit)
