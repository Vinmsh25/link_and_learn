"""
Skills app models - simple skill tracking.
"""
from django.db import models
from django.conf import settings


class Skill(models.Model):
    """A skill that users can teach or learn."""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class UserSkill(models.Model):
    """Tracks skills a user can teach or wants to learn."""
    
    SKILL_TYPE_CHOICES = [
        ('teach', 'Can Teach'),
        ('learn', 'Want to Learn'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_skills'
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='user_skills'
    )
    skill_type = models.CharField(max_length=10, choices=SKILL_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'skill', 'skill_type']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.name} - {self.skill.name} ({self.skill_type})"
