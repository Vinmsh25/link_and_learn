from django.contrib import admin
from .models import Skill, UserSkill


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)


@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ('user', 'skill', 'skill_type', 'created_at')
    list_filter = ('skill_type',)
