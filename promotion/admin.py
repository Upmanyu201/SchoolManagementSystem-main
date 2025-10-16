# admin.py
from django.contrib import admin
from .models import PromotionRule  # Import the model

@admin.register(PromotionRule)
class PromotionRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'min_marks', 'custom_method']  # Fields to display in the admin list view

    def custom_method(self, obj):
        return f"Custom: {obj.name}"

    custom_method.short_description = 'Custom Name'  # Description for the custom method column