from django.contrib import admin
from .models import MSG91Config, MessageLog

@admin.register(MSG91Config)
class MSG91ConfigAdmin(admin.ModelAdmin):
    list_display = ['sender_id', 'is_active', 'created_at']
    list_filter = ['is_active']

@admin.register(MessageLog)
class MessageLogAdmin(admin.ModelAdmin):
    list_display = ['recipient_name', 'recipient_phone', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['recipient_name', 'recipient_phone']
    readonly_fields = ['msg91_message_id', 'created_at', 'updated_at']