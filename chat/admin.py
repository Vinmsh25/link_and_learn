from django.contrib import admin
from .models import ChatMessage, DirectMessage


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'sender', 'content', 'created_at')
    list_filter = ('created_at',)


@admin.register(DirectMessage)
class DirectMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'content', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
