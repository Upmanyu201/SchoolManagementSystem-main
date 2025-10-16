from django.contrib import admin
from .models import SchoolProfile, Class, PromotionRule
from django.utils.safestring import mark_safe  

@admin.register(SchoolProfile)
class SchoolProfileAdmin(admin.ModelAdmin):
    list_display = ('school_name', 'principal_name', 'email', 'current_academic_session')
    readonly_fields = ('current_academic_session',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('school_name', 'principal_name', 'address', 'email', 'mobile', 'registration_number')
        }),
        ('Media', {
            'fields': ('logo', 'website', 'academic_calendar')
        }),
        ('Academic Session', {
            'fields': ('start_date', 'end_date', 'academic_session_start_month', 'current_academic_session')
        }),
    )

    def logo_preview(self, obj):
        if obj.logo:
            return mark_safe(f'<img src="{obj.logo.url}" width="100" />')
        return "No logo"
    logo_preview.short_description = 'Logo Preview'

class PromotionRuleInline(admin.TabularInline):
    model = PromotionRule
    fk_name = 'current_class'
    extra = 1

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_order')
    list_editable = ('display_order',)
    inlines = [PromotionRuleInline]

@admin.register(PromotionRule)
class PromotionRuleAdmin(admin.ModelAdmin):
    list_display = ('current_class', 'next_class', 'is_active')
    list_editable = ('is_active',)
    list_filter = ('is_active',)