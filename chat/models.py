"""
Chat app models.
"""
from django.db import models
from django.conf import settings


class ChatMessage(models.Model):
    """Chat message within a session."""
    
    session = models.ForeignKey(
        'users.Session',
        on_delete=models.CASCADE,
        related_name='chat_messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.name}: {self.content[:50]}"


class DirectMessage(models.Model):
    """Direct message between two users (pre-session chat)."""
    
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='direct_messages_sent'
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='direct_messages_received'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.name} -> {self.receiver.name}: {self.content[:30]}"
