# D:\School-Management-System\School-Management-System-main\students\models.py
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
from django.core.cache import cache
from django.utils.functional import cached_property
from django.db.models import Prefetch, Sum, Q
from datetime import timedelta
from django.utils import timezone
from core.models import BaseModel
from subjects.models import ClassSection
from core.validators import validate_phone_number, validate_aadhaar_number, validate_admission_number, validate_file_size, validate_file_extension
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class StudentManager(models.Manager):
    """Custom manager for optimized student queries"""
    
    def get_queryset(self):
        """Default optimized queryset - only active students by default"""
        return super().get_queryset().select_related('class_section').filter(status='ACTIVE')
    
    def all_statuses(self):
        """Get students with all statuses"""
        return super().get_queryset().select_related('class_section')
    
    def active(self):
        """Get only active students"""
        return self.filter(status='ACTIVE')
    
    def suspended(self):
        """Get only suspended students"""
        return self.all_statuses().filter(status='SUSPENDED')
    
    def archived(self):
        """Get only archived students"""
        return self.all_statuses().filter(status='ARCHIVED')
    
    def graduated(self):
        """Get only graduated students"""
        return self.all_statuses().filter(status='GRADUATED')
    
    def get_with_complete_data(self, admission_number):
        """Single query to load all student data with relationships"""
        return self.all_statuses().select_related(
            'class_section'
        ).prefetch_related(
            'fee_deposits',
            'finestudent_set__fine'
        ).get(admission_number=admission_number)
    
    def get_dashboard_data(self, admission_number):
        """Optimized query for dashboard with minimal data"""
        return self.all_statuses().select_related(
            'class_section'
        ).only(
            'admission_number', 'first_name', 'last_name', 'student_image',
            'mobile_number', 'email', 'due_amount', 'created_at', 'status',
            'class_section__class_name', 'class_section__section_name'
        ).get(admission_number=admission_number)
    
    def get_list_optimized(self, status_filter=None):
        """Optimized queryset for student list view with status filtering"""
        queryset = self.all_statuses().select_related('class_section').only(
            'id', 'admission_number', 'first_name', 'last_name',
            'mobile_number', 'email', 'due_amount', 'created_at', 'status',
            'class_section__class_name', 'class_section__section_name'
        )
        
        if status_filter and status_filter != '':
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('first_name', 'last_name')
    
    def search_students(self, query, status_filter=None):
        """Optimized search with indexed fields and status filtering"""
        from django.db.models import Q
        queryset = self.all_statuses().select_related('class_section').filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(admission_number__icontains=query) |
            Q(mobile_number__icontains=query)
        )
        
        if status_filter and status_filter != '':
            queryset = queryset.filter(status=status_filter)

        
        return queryset.only(
            'id', 'admission_number', 'first_name', 'last_name',
            'mobile_number', 'status', 'class_section__class_name'
        )[:100]  # Limit results
    
    def get_status_counts(self):
        """Get count of students by status with caching"""
        cache_key = "student_status_counts"
        counts = cache.get(cache_key)
        
        if counts is None:
            from django.db.models import Count
            counts = self.all_statuses().values('status').annotate(count=Count('id'))
            counts_dict = {item['status']: item['count'] for item in counts}
            
            # Ensure all statuses are represented
            final_counts = {
                'ACTIVE': counts_dict.get('ACTIVE', 0),
                'SUSPENDED': counts_dict.get('SUSPENDED', 0),
                'ARCHIVED': counts_dict.get('ARCHIVED', 0),
                'GRADUATED': counts_dict.get('GRADUATED', 0),
            }
            
            cache.set(cache_key, final_counts, 300)  # Cache for 5 minutes
            counts = final_counts
        
        return counts


class Student(BaseModel):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    RELIGION_CHOICES = [
        ('Hindu', 'Hindu'),
        ('Muslim', 'Muslim'),
        ('Christian', 'Christian'),
        ('Sikh', 'Sikh'),
        ('Other', 'Other'),
    ]

    CASTE_CHOICES = [
        ('General', 'General'),
        ('BC', 'BC'),
        ('EBC', 'EBC'),
        ('OBC', 'OBC'),
        ('SC', 'SC'),
        ('ST', 'ST'),
        ('Other', 'Other'),
    ]

    BLOOD_GROUP_CHOICES = [
        ('UNKN', 'UNKN'),
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
    ]

    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('SUSPENDED', 'Suspended'),
        ('ARCHIVED', 'Archived'),
        ('GRADUATED', 'Graduated'),
    ]

    admission_number = models.CharField(max_length=20, unique=True, verbose_name="Admission Number", validators=[validate_admission_number])
    first_name = models.CharField(max_length=50, verbose_name="First Name")
    last_name = models.CharField(max_length=50, verbose_name="Last Name")
    father_name = models.CharField(max_length=100, verbose_name="Father's Name")
    mother_name = models.CharField(max_length=100, verbose_name="Mother's Name")
    date_of_birth = models.DateField(verbose_name="Date of Birth")
    date_of_admission = models.DateField(verbose_name="Date of Admission")
    aadhaar_number = models.CharField(max_length=14, blank=True, null=True, validators=[validate_aadhaar_number])
    pen_number = models.CharField(max_length=11, blank=True, null=True)
    class_section = models.ForeignKey(ClassSection, on_delete=models.CASCADE, related_name='students', null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, verbose_name="Gender")
    
    # Legacy properties for backward compatibility
    @property
    def student_class(self):
        """Backward compatibility property"""
        return self.class_section
    
    @property
    def student_section(self):
        """Backward compatibility property"""
        return self.class_section
    religion = models.CharField(max_length=20, choices=RELIGION_CHOICES, verbose_name="Religion")
    caste_category = models.CharField(max_length=20, choices=CASTE_CHOICES, verbose_name="Caste Category")
    address = models.TextField(verbose_name="Address")
    mobile_number = models.CharField(
        max_length=10,
        validators=[validate_phone_number],
        verbose_name="Mobile Number"
    )
    email = models.EmailField(verbose_name="Email")
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES, verbose_name="Blood Group")
    student_image = models.ImageField(upload_to='students/images/', null=True, blank=True, validators=[validate_file_size, validate_file_extension])
    aadhar_card = models.FileField(upload_to='students/documents/', verbose_name="Aadhar Card", validators=[validate_file_size, validate_file_extension])
    transfer_certificate = models.FileField(upload_to='students/documents/', verbose_name="Transfer Certificate", validators=[validate_file_size, validate_file_extension])
    due_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE', verbose_name="Status")
    status_reason = models.TextField(blank=True, null=True, verbose_name="Status Change Reason")
    status_changed_date = models.DateTimeField(blank=True, null=True, verbose_name="Status Changed Date")
    status_changed_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="Status Changed By")
    
    objects = StudentManager()
    
    class Meta:
        indexes = [
            models.Index(fields=['admission_number']),
            models.Index(fields=['class_section']),
            models.Index(fields=['created_at']),
            models.Index(fields=['first_name', 'last_name']),
            models.Index(fields=['mobile_number']),
            models.Index(fields=['email']),
            models.Index(fields=['due_amount']),
            models.Index(fields=['status']),
            models.Index(fields=['status', 'class_section']),
        ]
        ordering = ['first_name', 'last_name']
    
    def update_due_amount(self):
        """Update due amount with auto-sync of new fees/fines"""
        try:
            from core.fee_calculation_engine import fee_engine
            # Auto-sync new fees and fines before calculating
            fee_engine.auto_sync_student_fees(self)
            # Clear cache to get fresh data
            self.invalidate_cache()
        except ImportError:
            pass

    def __str__(self):
        return f"{self.get_full_display_name()}"
    
    def save(self, *args, **kwargs):
        # Clean broken files before saving
        if self.pk:  # Only for existing records
            try:
                self.clean_broken_files()
            except Exception as e:
                logger.warning(f"File cleanup failed for {self.admission_number}: {e}")
        
        super().save(*args, **kwargs)
        # Invalidate cache when student data changes
        self.invalidate_cache()

    def get_full_display_name(self):
        return f"{self.first_name} {self.last_name} ({self.admission_number})"
    
    def get_full_name(self):
        """Get full name without admission number"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def name(self):
        """Compatibility property for legacy code"""
        return f"{self.first_name} {self.last_name}"
    
    @cached_property
    def financial_summary(self):
        """Complete financial overview with caching and auto-sync"""
        cache_key = f"financial_summary_{self.id}"
        summary = cache.get(cache_key)
        
        if summary is None:
            try:
                from core.fee_calculation_engine import fee_engine
                # Use the auto-sync version to detect new fees/fines
                summary = fee_engine.get_dashboard_summary(self)['financial_overview']
                # Also run auto-sync to ensure latest data
                fee_engine.auto_sync_student_fees(self)
            except ImportError:
                # Optimized fallback calculation
                from decimal import Decimal
                from django.db.models import Sum
                
                # Get fee deposits in single query
                paid_amount = self.fee_deposits.aggregate(
                    total=Sum('paid_amount')
                )['total'] or Decimal('0')
                
                carry_forward = self.due_amount or Decimal('0')
                current_session_dues = Decimal('7000.00')  # This should come from fee structure
                fines_total = self.unpaid_fines_total
                total_outstanding = carry_forward + current_session_dues + fines_total - paid_amount
                
                summary = {
                    'carry_forward': carry_forward,
                    'current_session_dues': current_session_dues,
                    'unpaid_fines': fines_total,
                    'paid_amount': paid_amount,
                    'total_outstanding': max(total_outstanding, Decimal('0'))
                }
            
            # Cache for 15 minutes
            cache.set(cache_key, summary, 900)
        
        return summary
    
    @property
    def total_balance(self):
        """Backward compatibility"""
        return self.financial_summary
    
    @cached_property
    def academic_summary(self):
        """Complete academic picture"""
        return {
            'class': self.class_section.class_name if self.class_section else 'N/A',
            'section': self.class_section.section_name if self.class_section else 'N/A',
            'attendance_percentage': self.get_attendance_percentage(),
            'latest_results': self.get_latest_exam_results()
        }
    
    def get_carry_forward_due(self):
        """Get carry forward amount - returns the manually set due_amount"""
        return self.due_amount
    
    @cached_property
    def unpaid_fines_total(self):
        """Get total unpaid fines with caching"""
        from decimal import Decimal
        try:
            from fines.models import FineStudent
            # Use select_related to avoid N+1 queries
            unpaid_fines = FineStudent.objects.select_related('fine').filter(
                student=self,
                is_paid=False
            )
            return sum(f.fine.amount for f in unpaid_fines) or Decimal('0')
        except (ImportError, AttributeError):
            return Decimal('0')
    
    def get_unpaid_fines_total(self):
        """Backward compatibility method"""
        return self.unpaid_fines_total
    
    @cached_property
    def attendance_percentage(self):
        """Calculate attendance percentage with caching"""
        cache_key = f"attendance_pct_{self.id}"
        percentage = cache.get(cache_key)
        
        if percentage is None:
            try:
                from attendance.models import Attendance
                from django.db.models import Count, Q
                
                # Single query with aggregation
                stats = Attendance.objects.filter(student=self).aggregate(
                    total=Count('id'),
                    present=Count('id', filter=Q(status='Present'))
                )
                
                total = stats['total'] or 0
                present = stats['present'] or 0
                percentage = round((present / total * 100), 2) if total > 0 else 0
                
                # Cache for 1 hour
                cache.set(cache_key, percentage, 3600)
            except:
                percentage = 0
        
        return percentage
    
    def get_attendance_percentage(self):
        """Backward compatibility method"""
        return self.attendance_percentage
    
    def get_dashboard_data(self):
        """Optimized method for dashboard data using service layer"""
        try:
            from students.services import StudentDashboardService
            return StudentDashboardService.get_complete_dashboard_data(self)
        except ImportError:
            # Fallback to basic dashboard data
            cache_key = f"student_dashboard_{self.admission_number}"
            data = cache.get(cache_key)
            
            if not data:
                data = {
                    'profile': self.get_profile_data(),
                    'financial': self.financial_summary,
                    'academic': self.academic_summary,
                    'recent_activities': self.get_recent_activities()[:10]
                }
                cache.set(cache_key, data, 300)  # 5 minutes
            
            return data
    
    def get_profile_data(self):
        """Basic profile information"""
        return {
            'admission_number': self.admission_number,
            'name': self.name,
            'class': self.class_section.class_name if self.class_section else 'N/A',
            'section': self.class_section.section_name if self.class_section else 'N/A',
            'photo': self.get_image_url(),
            'mobile': self.mobile_number,
            'email': self.email
        }
    
    @cached_property
    def recent_activities(self):
        """Get recent student activities with caching"""
        cache_key = f"recent_activities_{self.id}"
        activities = cache.get(cache_key)
        
        if activities is None:
            activities = []
            
            # Recent fee payments - optimized query
            recent_payments = self.fee_deposits.filter(
                deposit_date__gte=timezone.now().date() - timedelta(days=30)
            ).only(
                'deposit_date', 'paid_amount', 'receipt_no'
            ).order_by('-deposit_date')[:5]
            
            for payment in recent_payments:
                activities.append({
                    'type': 'payment',
                    'date': payment.deposit_date,
                    'description': f'Fee payment: ₹{payment.paid_amount}',
                    'icon': 'fas fa-credit-card',
                    'color': 'success'
                })
            
            activities = sorted(activities, key=lambda x: x['date'], reverse=True)
            
            # Cache for 10 minutes
            cache.set(cache_key, activities, 600)
        
        return activities
    
    def get_recent_activities(self):
        """Backward compatibility method"""
        return self.recent_activities
    
    def get_unified_timeline(self):
        """Chronological view of all student activities"""
        events = []
        
        # Fee payments
        for deposit in self.fee_deposits.all():
            events.append({
                'type': 'payment',
                'date': deposit.deposit_date,
                'description': f'Fee payment: ₹{deposit.paid_amount}',
                'data': deposit
            })
        
        # Attendance records (recent)
        try:
            from attendance.models import Attendance
            recent_attendance = Attendance.objects.filter(
                student=self,
                date__gte=timezone.now().date() - timedelta(days=30)
            )
            for att in recent_attendance:
                events.append({
                    'type': 'attendance',
                    'date': att.date,
                    'description': f'Attendance: {att.status}',
                    'data': att
                })
        except ImportError:
            pass
        
        return sorted(events, key=lambda x: x['date'], reverse=True)
    
    def get_image_url(self):
        """Get student image URL with fallback to default avatar"""
        if self.student_image and hasattr(self.student_image, 'url') and self.student_image.url:
            try:
                # Check if file exists
                if self.student_image.storage.exists(self.student_image.name):
                    return self.student_image.url
            except Exception as e:
                # Log missing file and clear the field
                logger.warning(f"Missing student image file for {self.admission_number}: {e}")
                # Clear the broken file reference
                self.student_image = None
                self.save(update_fields=['student_image'])
        # Return default avatar URL
        return '/static/images/default-avatar.svg'
    
    def clean_broken_files(self):
        """Clean up all broken file references"""
        fields_to_clear = []
        
        # Check all file fields
        for field_name in ['student_image', 'aadhar_card', 'transfer_certificate']:
            field_value = getattr(self, field_name)
            if field_value:
                try:
                    if not field_value.storage.exists(field_value.name):
                        logger.warning(f"Missing {field_name} file for {self.admission_number}: {field_value.name}")
                        setattr(self, field_name, None)
                        fields_to_clear.append(field_name)
                except Exception as e:
                    logger.warning(f"Error checking {field_name} for {self.admission_number}: {e}")
                    setattr(self, field_name, None)
                    fields_to_clear.append(field_name)
        
        if fields_to_clear:
            self.save(update_fields=fields_to_clear)
    
    @property
    def image_url(self):
        """Property for template access"""
        return self.get_image_url()
    
    def get_last_payment(self):
        """Get last payment details"""
        try:
            last_payment = self.fee_deposits.latest('deposit_date')
            return {
                'amount': last_payment.paid_amount,
                'date': last_payment.deposit_date,
                'receipt_no': last_payment.receipt_no
            }
        except:
            return None
    
    def get_latest_exam_results(self):
        """Get latest exam results"""
        try:
            # This would need to be implemented based on your exam system
            return []
        except:
            return []
    
    def change_status(self, new_status, reason, changed_by):
        """Change student status with audit trail"""
        if new_status not in dict(self.STATUS_CHOICES):
            raise ValueError(f"Invalid status: {new_status}")
        
        old_status = self.status
        self.status = new_status
        self.status_reason = reason
        self.status_changed_date = timezone.now()
        self.status_changed_by = str(changed_by)
        self.save(update_fields=['status', 'status_reason', 'status_changed_date', 'status_changed_by'])
        
        # Log status change
        logger.info(f"Student {self.admission_number} status changed from {old_status} to {new_status} by {changed_by}")
        
        # Clear cache
        self.invalidate_cache()
    
    def get_status_display_info(self):
        """Get status with color and icon for UI"""
        status_info = {
            'ACTIVE': {'color': 'green', 'icon': 'user-check', 'label': 'Active'},
            'SUSPENDED': {'color': 'yellow', 'icon': 'pause', 'label': 'Suspended'},
            'ARCHIVED': {'color': 'gray', 'icon': 'archive', 'label': 'Archived'},
            'GRADUATED': {'color': 'blue', 'icon': 'graduation-cap', 'label': 'Graduated'},
        }
        return status_info.get(self.status, status_info['ACTIVE'])
    
    def invalidate_cache(self):
        """Clear all cached data for this student"""
        cache_keys = [
            f"student_dashboard_{self.admission_number}",
            f"student_fees_{self.admission_number}",
            f"student_activities_{self.admission_number}",
            f"financial_summary_{self.id}",
            f"attendance_pct_{self.id}",
            f"recent_activities_{self.id}",
            f"students_list_{self.id}",  # Clear list cache for any user
            f"student_status_counts",  # Clear status counts cache
        ]
        cache.delete_many(cache_keys)
        
        # Clear property caches
        if hasattr(self, '_financial_summary'):
            delattr(self, '_financial_summary')
        if hasattr(self, '_attendance_percentage'):
            delattr(self, '_attendance_percentage')
        if hasattr(self, '_recent_activities'):
            delattr(self, '_recent_activities')
        if hasattr(self, '_unpaid_fines_total'):
            delattr(self, '_unpaid_fines_total')


class StudentEnrollment(BaseModel):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    enrollment_date = models.DateField()
    class_name = models.CharField(max_length=50)
    section = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.student.first_name} {self.student.last_name} - {self.class_name}"
    
