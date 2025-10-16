from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User
from students.models import Student, Class
from fees.models import FeesGroup, FeesType
from student_fees.models import FeeDeposit
from transport.models import TransportAssignment, Stoppage, Route
from subjects.models import Subject
from datetime import date, timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
from .views import fees_report

class FeesReportTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='admin', 
            password='password',
            is_staff=True
        )
        
        # Create test data
        self.class1 = Class.objects.create(name='Class 1')
        self.class2 = Class.objects.create(name='Class 2')
        
        self.student1 = Student.objects.create(
            first_name='John',
            last_name='Doe',
            student_class=self.class1,
            due_amount=1000
        )
        self.student2 = Student.objects.create(
            first_name='Jane',
            last_name='Smith',
            student_class=self.class2,
            due_amount=500
        )
        
        # Create fee groups and types
        self.tuition_fee_group = FeesGroup.objects.create(
            fee_group='Monthly',
            group_type='Tuition Fee',
            fee_type='Class Based',
            related_class=self.class1
        )
        
        self.admission_fee_group = FeesGroup.objects.create(
            fee_group='One Time',
            group_type='Admission Fees',
            fee_type='General'
        )
        
        # Create fee types
        self.tuition_fee = FeesType.objects.create(
            fee_group=self.tuition_fee_group,
            group_type='Tuition Fee',
            fee_type='Class Based',
            amount_type='Fixed',
            amount=1000,
            class_name='Class 1'
        )
        
        self.admission_fee = FeesType.objects.create(
            fee_group=self.admission_fee_group,
            group_type='Admission Fees',
            fee_type='General',
            amount_type='Fixed',
            amount=500
        )
        
        # Create transport data
        self.route = Route.objects.create(name='Route 1')
        self.stoppage = Stoppage.objects.create(
            route=self.route,
            name='Stop 1'
        )
        self.transport_assignment = TransportAssignment.objects.create(
            student=self.student1,
            route=self.route,
            stoppage=self.stoppage
        )
        
        self.transport_fee_group = FeesGroup.objects.create(
            fee_group='Monthly',
            group_type='Transport',
            fee_type='Stoppage Based',
            related_stoppage=self.stoppage
        )
        
        self.transport_fee = FeesType.objects.create(
            fee_group=self.transport_fee_group,
            group_type='Transport',
            fee_type='Stoppage Based',
            amount_type='Fixed',
            amount=300,
            related_stoppage=self.stoppage
        )
        
        # Create fee deposits
        FeeDeposit.objects.create(
            student=self.student1,
            paid_amount=500,
            payment_mode='Cash',
            deposit_date=date.today()
        )
        FeeDeposit.objects.create(
            student=self.student2,
            paid_amount=300,
            payment_mode='Online',
            deposit_date=date.today() - timedelta(days=1)
        )

    def test_fees_report_view(self):
        url = reverse('reports:fees_report')
        request = self.factory.get(url)
        request.user = self.user
        
        response = fees_report(request)
        self.assertEqual(response.status_code, 200)
        
        # Test context data
        self.assertIn('report_data', response.context_data)
        self.assertIn('page_obj', response.context_data)
        self.assertIn('payment_summary', response.context_data)
        
    def test_pagination(self):
        # Create more students to test pagination
        for i in range(15):
            Student.objects.create(
                first_name=f'Student{i}',
                last_name=f'Test{i}',
                student_class=self.class1
            )
            
        url = reverse('reports:fees_report')
        request = self.factory.get(url)
        request.user = self.user
        
        response = fees_report(request)
        self.assertEqual(len(response.context_data['page_obj']), 10)
        
        # Test page 2
        request = self.factory.get(url + '?page=2')
        request.user = self.user
        response = fees_report(request)
        self.assertEqual(len(response.context_data['page_obj']), 7)  # 17 total students
        
    def test_class_filter(self):
        url = reverse('reports:fees_report') + f'?class={self.class1.id}'
        request = self.factory.get(url)
        request.user = self.user
        
        response = fees_report(request)
        report_data = response.context_data['report_data']
        
        # Should only include students from Class 1
        self.assertEqual(len(report_data), 1)
        self.assertEqual(report_data[0]['name'], 'John Doe')
        
    def test_date_filter(self):
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        url = reverse('reports:fees_report') + f'?from={yesterday}&to={today}'
        request = self.factory.get(url)
        request.user = self.user
        
        response = fees_report(request)
        payment_summary = response.context_data['payment_summary']
        
        # Should include both payments (one today, one yesterday)
        self.assertEqual(payment_summary['Cash'], 500)
        self.assertEqual(payment_summary['Online'], 300)
        
    def test_fee_calculations(self):
        url = reverse('reports:fees_report')
        request = self.factory.get(url)
        request.user = self.user
        
        response = fees_report(request)
        report_data = response.context_data['report_data']
        
        # Student 1 should have tuition + admission + transport fees
        student1_data = next(s for s in report_data if s['name'] == 'John Doe')
        self.assertEqual(student1_data['current_fees'], 1800)  # 1000 + 500 + 300
        
        # Student 2 should only have admission fee
        student2_data = next(s for s in report_data if s['name'] == 'Jane Smith')
        self.assertEqual(student2_data['current_fees'], 500)
        
    def test_export_excel(self):
        url = reverse('reports:fees_report') + '?export=excel'
        request = self.factory.get(url)
        request.user = self.user
        
        response = fees_report(request)
        self.assertEqual(response['Content-Type'], 'application/ms-excel')
        self.assertIn('attachment', response['Content-Disposition'])
        
    def test_export_pdf(self):
        url = reverse('reports:fees_report') + '?export=pdf'
        request = self.factory.get(url)
        request.user = self.user
        
        response = fees_report(request)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment', response['Content-Disposition'])
        
    def test_payment_mode_summary(self):
        url = reverse('reports:fees_report') + '?mode_report=today'
        request = self.factory.get(url)
        request.user = self.user
        
        response = fees_report(request)
        payment_summary = response.context_data['payment_summary']
        
        # Only today's payment (student1's cash payment)
        self.assertEqual(payment_summary['Cash'], 500)
        self.assertEqual(payment_summary['Online'], 0)  # Yesterday's payment not included