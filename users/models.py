from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.cache import cache
import json

class CustomUser(AbstractUser):
    """Custom user model extending Django's AbstractUser"""
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    mobile = models.CharField(max_length=15, unique=True, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    
    # Fix reverse accessor conflicts
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    
    def __str__(self):
        return self.username
    
    def delete(self, *args, **kwargs):
        """Custom delete to handle foreign key constraints"""
        # Delete related module permissions first
        try:
            if hasattr(self, 'module_permissions'):
                self.module_permissions.delete()
        except Exception:
            pass
        
        # Then delete the user
        super().delete(*args, **kwargs)

class UserModulePermission(models.Model):
    """2025 Industry Standard: Role-based module access control"""
    
    user = models.OneToOneField('CustomUser', on_delete=models.CASCADE, related_name='module_permissions')
    
    # Core Academic Modules
    students_view = models.BooleanField(default=False, verbose_name="Students View")
    students_edit = models.BooleanField(default=False, verbose_name="Students Edit")
    
    teachers_view = models.BooleanField(default=False, verbose_name="Teachers View")
    teachers_edit = models.BooleanField(default=False, verbose_name="Teachers Edit")
    
    # Financial Modules
    fees_view = models.BooleanField(default=False, verbose_name="Fees View")
    fees_edit = models.BooleanField(default=False, verbose_name="Fees Edit")
    
    payments_view = models.BooleanField(default=False, verbose_name="Payments View")
    payments_edit = models.BooleanField(default=False, verbose_name="Payments Edit")
    
    # Academic Modules
    attendance_view = models.BooleanField(default=False, verbose_name="Attendance View")
    attendance_edit = models.BooleanField(default=False, verbose_name="Attendance Edit")
    
    # Administrative Modules
    transport_view = models.BooleanField(default=False, verbose_name="Transport View")
    transport_edit = models.BooleanField(default=False, verbose_name="Transport Edit")
    
    reports_view = models.BooleanField(default=False, verbose_name="Reports View")
    reports_edit = models.BooleanField(default=False, verbose_name="Reports Edit")
    
    # System Modules
    users_view = models.BooleanField(default=False, verbose_name="Users View")
    users_edit = models.BooleanField(default=False, verbose_name="Users Edit")
    
    settings_view = models.BooleanField(default=False, verbose_name="Settings View")
    settings_edit = models.BooleanField(default=False, verbose_name="Settings Edit")
    
    # Missing Modules
    subjects_view = models.BooleanField(default=False, verbose_name="Subjects View")
    subjects_edit = models.BooleanField(default=False, verbose_name="Subjects Edit")
    
    messaging_view = models.BooleanField(default=False, verbose_name="Messaging View")
    messaging_edit = models.BooleanField(default=False, verbose_name="Messaging Edit")
    
    promotion_view = models.BooleanField(default=False, verbose_name="Promotion View")
    promotion_edit = models.BooleanField(default=False, verbose_name="Promotion Edit")
    
    backup_view = models.BooleanField(default=False, verbose_name="Backup View")
    backup_edit = models.BooleanField(default=False, verbose_name="Backup Edit")
    
    fines_view = models.BooleanField(default=False, verbose_name="Fines View")
    fines_edit = models.BooleanField(default=False, verbose_name="Fines Edit")
    
    school_profile_view = models.BooleanField(default=False, verbose_name="School Profile View")
    school_profile_edit = models.BooleanField(default=False, verbose_name="School Profile Edit")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Module Permission"
        verbose_name_plural = "User Module Permissions"
        db_table = 'users_module_permissions'
    
    def __str__(self):
        return f"{self.user.username} - Module Permissions"
    
    @classmethod
    def get_user_permissions(cls, user):
        """Get cached user permissions with fallback"""
        if user.is_superuser:
            return cls._get_superuser_permissions()
        
        cache_key = f"user_permissions_{user.id}"
        permissions = cache.get(cache_key)
        
        if permissions is None:
            try:
                perm_obj = cls.objects.get(user=user)
                permissions = cls._serialize_permissions(perm_obj)
            except cls.DoesNotExist:
                permissions = cls._get_default_permissions()
            
            cache.set(cache_key, permissions, 300)  # 5 min cache
        
        return permissions
    
    @classmethod
    def _get_superuser_permissions(cls):
        """Superuser has all permissions"""
        modules = ['students', 'teachers', 'subjects', 'fees', 'payments', 
                  'fines', 'attendance', 'transport', 'reports', 'messaging', 
                  'promotion', 'users', 'settings', 'backup', 'school_profile']
        return {module: {'view': True, 'edit': True} for module in modules}
    
    @classmethod
    def _get_default_permissions(cls):
        """Default: no permissions for regular users"""
        modules = ['students', 'teachers', 'subjects', 'fees', 'payments', 
                  'fines', 'attendance', 'transport', 'reports', 'messaging', 
                  'promotion', 'users', 'settings', 'backup', 'school_profile']
        return {module: {'view': False, 'edit': False} for module in modules}
    
    @classmethod
    def _serialize_permissions(cls, perm_obj):
        """Convert model instance to dict"""
        return {
            'students': {'view': perm_obj.students_view, 'edit': perm_obj.students_edit},
            'teachers': {'view': perm_obj.teachers_view, 'edit': perm_obj.teachers_edit},
            'subjects': {'view': perm_obj.subjects_view, 'edit': perm_obj.subjects_edit},
            'fees': {'view': perm_obj.fees_view, 'edit': perm_obj.fees_edit},
            'payments': {'view': perm_obj.payments_view, 'edit': perm_obj.payments_edit},
            'fines': {'view': perm_obj.fines_view, 'edit': perm_obj.fines_edit},
            'attendance': {'view': perm_obj.attendance_view, 'edit': perm_obj.attendance_edit},
            'transport': {'view': perm_obj.transport_view, 'edit': perm_obj.transport_edit},
            'reports': {'view': perm_obj.reports_view, 'edit': perm_obj.reports_edit},
            'messaging': {'view': perm_obj.messaging_view, 'edit': perm_obj.messaging_edit},
            'promotion': {'view': perm_obj.promotion_view, 'edit': perm_obj.promotion_edit},
            'users': {'view': perm_obj.users_view, 'edit': perm_obj.users_edit},
            'settings': {'view': perm_obj.settings_view, 'edit': perm_obj.settings_edit},
            'backup': {'view': perm_obj.backup_view, 'edit': perm_obj.backup_edit},
            'school_profile': {'view': perm_obj.school_profile_view, 'edit': perm_obj.school_profile_edit},
        }
    
    def save(self, *args, **kwargs):
        """Clear cache on save"""
        super().save(*args, **kwargs)
        cache_key = f"user_permissions_{self.user.id}"
        cache.delete(cache_key)
    
    def has_module_access(self, module_name, permission_type='view'):
        """Check if user has specific module permission"""
        field_name = f"{module_name}_{permission_type}"
        return getattr(self, field_name, False)
    
    @classmethod
    def get_or_create_for_user(cls, user, **permissions):
        """Get or create permissions for user - prevents duplicate errors"""
        try:
            obj, created = cls.objects.get_or_create(
                user=user,
                defaults=permissions
            )
            if not created and permissions:
                # Update existing permissions
                for field, value in permissions.items():
                    setattr(obj, field, value)
                obj.save()
            return obj, created
        except Exception:
            # Fallback: try to get existing
            try:
                return cls.objects.get(user=user), False
            except cls.DoesNotExist:
                # Create with defaults if all else fails
                return cls.objects.create(user=user, **permissions), True