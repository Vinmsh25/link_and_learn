from django.contrib import admin
from .models import LearningRequest


@admin.register(LearningRequest)
class LearningRequestAdmin(admin.ModelAdmin):
    list_display = ('creator', 'topic_to_learn', 'topic_to_teach', 'ok_with_just_learning', 'is_completed', 'created_at')
    list_filter = ('is_completed', 'ok_with_just_learning', 'created_at')
    search_fields = ('topic_to_learn', 'topic_to_teach', 'creator__email', 'creator__name')
