from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserModulePermission

@admin.register(UserModulePermission)
class UserModulePermissionAdmin(admin.ModelAdmin):
    """2025 Industry Standard: Enhanced admin interface for module permissions"""
    
    list_display = [
        'user', 'get_full_name', 'get_active_modules', 'get_edit_modules', 
        'created_at', 'updated_at'
    ]
    list_filter = [
        'created_at', 'updated_at',
        'students_view', 'students_edit',
        'fees_view', 'fees_edit',
        'users_view', 'users_edit',
        'teachers_view', 'teachers_edit'
    ]
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Academic Modules', {
            'fields': (
                ('students_view', 'students_edit'),
                ('teachers_view', 'teachers_edit'),
                ('subjects_view', 'subjects_edit'),
            ),
            'classes': ['collapse']
        }),
        ('Financial Modules', {
            'fields': (
                ('fees_view', 'fees_edit'),
                ('payments_view', 'payments_edit'),
                ('fines_view', 'fines_edit'),
            ),
            'classes': ['collapse']
        }),
        ('Operations', {
            'fields': (
                ('attendance_view', 'attendance_edit'),
                ('transport_view', 'transport_edit'),
                ('promotion_view', 'promotion_edit'),
            ),
            'classes': ['collapse']
        }),
        ('Communication & Reports', {
            'fields': (
                ('reports_view', 'reports_edit'),
                ('messaging_view', 'messaging_edit'),
            ),
            'classes': ['collapse']
        }),
        ('System Management', {
            'fields': (
                ('users_view', 'users_edit'),
                ('settings_view', 'settings_edit'),
                ('backup_view', 'backup_edit'),
                ('school_profile_view', 'school_profile_edit'),
            ),
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )
    
    def get_full_name(self, obj):
        """Display user's full name"""
        return obj.user.get_full_name() or obj.user.username
    get_full_name.short_description = 'Full Name'
    
    def get_active_modules(self, obj):
        """Count modules with view access"""
        modules = ['students', 'teachers', 'subjects', 'fees', 'payments', 'fines',
                  'attendance', 'transport', 'reports', 'messaging', 'promotion', 
                  'users', 'settings', 'backup', 'school_profile']
        count = sum(1 for module in modules if getattr(obj, f"{module}_view", False))
        return f"{count}/{len(modules)}"
    get_active_modules.short_description = 'View Access'
    
    def get_edit_modules(self, obj):
        """Count modules with edit access"""
        modules = ['students', 'teachers', 'subjects', 'fees', 'payments', 'fines',
                  'attendance', 'transport', 'reports', 'messaging', 'promotion', 
                  'users', 'settings', 'backup', 'school_profile']
        count = sum(1 for module in modules if getattr(obj, f"{module}_edit", False))
        return f"{count}/{len(modules)}"
    get_edit_modules.short_description = 'Edit Access'
    
    actions = ['grant_basic_access', 'grant_teacher_access', 'revoke_all_access']
    
    def grant_basic_access(self, request, queryset):
        """Grant basic view access to common modules"""
        for permission in queryset:
            permission.students_view = True
            permission.attendance_view = True
            permission.reports_view = True
            permission.save()
        self.message_user(request, f"Basic access granted to {queryset.count()} users.")
    grant_basic_access.short_description = "Grant basic access (Students, Attendance, Reports)"
    
    def grant_teacher_access(self, request, queryset):
        """Grant teacher-level access"""
        for permission in queryset:
            permission.students_view = True
            permission.attendance_view = True
            permission.attendance_edit = True
            permission.subjects_view = True
            permission.reports_view = True
            permission.save()
        self.message_user(request, f"Teacher access granted to {queryset.count()} users.")
    grant_teacher_access.short_description = "Grant teacher access"
    
    def revoke_all_access(self, request, queryset):
        """Revoke all module access"""
        modules = ['students', 'teachers', 'subjects', 'fees', 'payments', 'fines',
                  'attendance', 'transport', 'reports', 'messaging', 'promotion', 
                  'users', 'settings', 'backup', 'school_profile']
        
        for permission in queryset:
            for module in modules:
                setattr(permission, f"{module}_view", False)
                setattr(permission, f"{module}_edit", False)
            permission.save()
        
        self.message_user(request, f"All access revoked for {queryset.count()} users.")
    revoke_all_access.short_description = "Revoke all access"

# Extend the default User admin to show module permissions
class UserAdmin(BaseUserAdmin):
    """Enhanced User admin with module permission info"""
    
    def get_inline_instances(self, request, obj=None):
        inlines = super().get_inline_instances(request, obj)
        if obj:
            inlines.append(UserModulePermissionInline(self.model, self.admin_site))
        return inlines

class UserModulePermissionInline(admin.StackedInline):
    """Inline admin for module permissions"""
    model = UserModulePermission
    extra = 0
    can_delete = False
    
    fieldsets = (
        ('Quick Access', {
            'fields': (
                ('students_view', 'fees_view', 'attendance_view'),
                ('students_edit', 'fees_edit', 'attendance_edit'),
            )
        }),
    )

# Register CustomUser with enhanced admin
from .models import CustomUser
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_staff']
    list_filter = ['role', 'is_staff', 'is_superuser', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'mobile', 'profile_picture')}),
    )