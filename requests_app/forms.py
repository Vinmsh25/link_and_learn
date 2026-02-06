"""
Learning Request forms.
"""
from django import forms
from .models import LearningRequest


class LearningRequestForm(forms.ModelForm):
    """Form for creating a learning request."""
    
    class Meta:
        model = LearningRequest
        fields = ('topic_to_learn', 'topic_to_teach', 'ok_with_just_learning')
        widgets = {
            'topic_to_learn': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'What do you want to learn?',
                'required': True
            }),
            'topic_to_teach': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'What can you teach in exchange? (optional)'
            }),
            'ok_with_just_learning': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
        }
        labels = {
            'topic_to_learn': 'I want to learn',
            'topic_to_teach': 'I can teach',
            'ok_with_just_learning': "I'm ok with just learning (will pay credits)",
        }
