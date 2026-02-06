"""
Skills views.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from .models import Skill


@login_required
def skills_list(request):
    """List all available skills."""
    skills = Skill.objects.all()
    return render(request, 'skills/list.html', {'skills': skills})
