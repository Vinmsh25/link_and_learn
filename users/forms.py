"""
User forms for authentication and profile management.
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from .models import Review

User = get_user_model()


class SignupForm(UserCreationForm):
    """Custom signup form with styled fields."""
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your email',
            'autocomplete': 'email'
        })
    )
    name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your full name',
            'autocomplete': 'name'
        })
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Create a password',
            'autocomplete': 'new-password'
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Confirm your password',
            'autocomplete': 'new-password'
        })
    )
    
    class Meta:
        model = User
        fields = ('email', 'name', 'password1', 'password2')


class LoginForm(AuthenticationForm):
    """Custom login form with styled fields."""
    
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your email',
            'autocomplete': 'email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password'
        })
    )


class ProfileForm(forms.ModelForm):
    """Form for editing user profile."""
    
    class Meta:
        model = User
        fields = ('name', 'availability')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Your name'
            }),
            'availability': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., Mon-Fri 9am-5pm'
            }),
        }


class AvailabilityForm(forms.Form):
    """Form for setting availability on logout."""
    
    availability = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'When are you available? e.g., Mon-Fri 9am-5pm'
        })
    )


class DonationForm(forms.Form):
    """Form for donating credits to the bank."""
    
    amount = forms.DecimalField(
        min_value=1,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': 'Amount to donate',
            'min': '1',
            'step': '0.5'
        })
    )


class ReviewForm(forms.ModelForm):
    """Form for submitting session reviews."""
    
    class Meta:
        model = Review
        fields = ('rating', 'comment')
        widgets = {
            'rating': forms.Select(
                choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)],
                attrs={'class': 'form-select'}
            ),
            'comment': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Share your experience (optional)',
                'rows': 3
            }),
        }
