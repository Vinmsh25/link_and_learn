"""
Learning Request models.
"""
from django.db import models
from django.conf import settings


class LearningRequest(models.Model):
    """
    Learning Request Post model.
    Users create posts when they want to learn something.
    """
    
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='learning_requests'
    )
    topic_to_learn = models.CharField(
        max_length=255,
        help_text='Topic the user wants to learn'
    )
    topic_to_teach = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='Topic the user can teach in exchange (optional)'
    )
    ok_with_just_learning = models.BooleanField(
        default=False,
        help_text='User is okay with just learning (paying credits)'
    )
    bounty_enabled = models.BooleanField(
        default=False,
        help_text='User is willing to pay extra credits as bounty'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(
        default=False,
        help_text='Whether this request has been fulfilled'
    )
    
    class Meta:
        verbose_name = 'learning request'
        verbose_name_plural = 'learning requests'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.creator.name} wants to learn: {self.topic_to_learn}"
    
    @classmethod
    def get_active_requests(cls):
        """Return all active (not completed) requests."""
        return cls.objects.filter(is_completed=False)
    
    def mark_completed(self):
        """Mark this request as completed."""
        self.is_completed = True
        self.save(update_fields=['is_completed'])
