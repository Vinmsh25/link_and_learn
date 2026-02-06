"""
User views for authentication, profiles, and bank operations.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from datetime import timedelta
from decimal import Decimal
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .forms import SignupForm, LoginForm, ProfileForm, AvailabilityForm, DonationForm, ReviewForm
from .models import Bank, CreditTransaction, Session, SessionTimer, Review
from requests_app.models import LearningRequest

User = get_user_model()


def home(request):
    """Landing page."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')


def signup_view(request):
    """User signup."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Record signup bonus transaction
            CreditTransaction.objects.create(
                user=user,
                amount=Decimal(str(settings.INITIAL_USER_CREDITS)),
                transaction_type='SIGNUP',
                balance_after=user.credits,
                description='Welcome bonus credits'
            )
            login(request, user)
            messages.success(request, f'Welcome to Link & Learn, {user.name}! You received {settings.INITIAL_USER_CREDITS} credits.')
            return redirect('dashboard')
    else:
        form = SignupForm()
    
    return render(request, 'auth/signup.html', {'form': form})


def login_view(request):
    """User login."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            user.is_online = True
            user.save(update_fields=['is_online'])
            login(request, user)
            messages.success(request, f'Welcome back, {user.name}!')
            return redirect('dashboard')
    else:
        form = LoginForm()
    
    return render(request, 'auth/login.html', {'form': form})


@login_required
def logout_view(request):
    """Logout with availability prompt."""
    user = request.user
    has_active_posts = LearningRequest.objects.filter(creator=user, is_completed=False).exists()
    
    if request.method == 'POST':
        form = AvailabilityForm(request.POST)
        if form.is_valid():
            user.availability = form.cleaned_data.get('availability', '')
            user.is_online = False
            user.last_seen = timezone.now()
            user.save(update_fields=['availability', 'is_online', 'last_seen'])
            logout(request)
            messages.success(request, 'You have been logged out.')
            return redirect('home')
    else:
        form = AvailabilityForm(initial={'availability': user.availability})
    
    return render(request, 'auth/logout.html', {
        'form': form,
        'has_active_posts': has_active_posts
    })


@login_required
def dashboard(request):
    """Main dashboard view."""
    user = request.user
    # recent_requests removed as per user request
    my_requests = LearningRequest.objects.filter(creator=user, is_completed=False)
    
    return render(request, 'dashboard/index.html', {
        'my_requests': my_requests,
    })


@login_required
def profile_view(request, user_id=None):
    """View user profile."""
    if user_id:
        profile_user = get_object_or_404(User, pk=user_id)
    else:
        profile_user = request.user
    
    reviews = Review.objects.filter(reviewee=profile_user).select_related('reviewer', 'session')[:10]
    is_own_profile = profile_user == request.user
    
    return render(request, 'profile/view.html', {
        'profile_user': profile_user,
        'reviews': reviews,
        'is_own_profile': is_own_profile,
    })


@login_required
def edit_profile(request):
    """Edit own profile."""
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)
    
    return render(request, 'profile/edit.html', {'form': form})


@login_required
def credit_history(request):
    """View credit transaction history."""
    transactions = CreditTransaction.objects.filter(user=request.user)[:50]
    return render(request, 'profile/credit_history.html', {'transactions': transactions})


@login_required
def bank_view(request):
    """Bank page with donation and support options."""
    bank = Bank.get_instance()
    user = request.user
    
    # Check support eligibility
    can_request_support = True
    support_amount = bank.get_support_amount(user.credits)
    cooldown_message = None
    
    if support_amount == 0:
        can_request_support = False
        cooldown_message = "You have more than 3 credits and are not eligible for support."
    elif user.last_support_request:
        cooldown_end = user.last_support_request + timedelta(hours=settings.SUPPORT_CREDIT_COOLDOWN_HOURS)
        if timezone.now() < cooldown_end:
            can_request_support = False
            cooldown_message = f"You can request support again after {cooldown_end.strftime('%Y-%m-%d %H:%M')}."
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'donate':
            form = DonationForm(request.POST)
            if form.is_valid():
                amount = form.cleaned_data['amount']
                if amount > user.credits:
                    messages.error(request, 'Insufficient credits.')
                else:
                    CreditTransaction.record_transaction(
                        user=user,
                        amount=-amount,
                        transaction_type='DONATION',
                        description='Donation to Bank'
                    )
                    bank.add_credits(amount)
                    messages.success(request, f'Thank you for donating {amount} credits!')
                    return redirect('bank')
        
        elif action == 'support' and can_request_support and support_amount > 0:
            if bank.total_credits >= support_amount:
                bank.deduct_credits(support_amount)
                CreditTransaction.record_transaction(
                    user=user,
                    amount=support_amount,
                    transaction_type='SUPPORT',
                    description=f'Bank support ({support_amount} credits)'
                )
                user.last_support_request = timezone.now()
                user.save(update_fields=['last_support_request'])
                messages.success(request, f'You received {support_amount} support credits!')
            else:
                messages.error(request, 'Bank has insufficient funds.')
            return redirect('bank')
    
    donation_form = DonationForm()
    
    return render(request, 'profile/bank.html', {
        'bank': bank,
        'donation_form': donation_form,
        'can_request_support': can_request_support,
        'support_amount': support_amount,
        'cooldown_message': cooldown_message,
    })


@login_required
def session_view(request, session_id):
    """Session page with tools."""
    session = get_object_or_404(Session, pk=session_id)
    
    # Verify user is part of session
    if request.user not in [session.user1, session.user2]:
        messages.error(request, 'You are not part of this session.')
        return redirect('dashboard')
    
    partner = session.user2 if request.user == session.user1 else session.user1
    active_timer = session.get_active_timer()
    
    # Calculate accumulated teaching time for the current user in this session
    teaching_seconds = session.get_teaching_time(request.user)
    
    return render(request, 'dashboard/session.html', {
        'session': session,
        'partner': partner,
        'active_timer': active_timer,
        'is_my_timer_running': active_timer and active_timer.teacher == request.user,
        'teaching_seconds': teaching_seconds,
        'active_timer_start': int(active_timer.start_time.timestamp()) if active_timer and active_timer.teacher == request.user else None,
    })


@login_required
@require_POST
def start_timer(request, session_id):
    """Start teaching timer."""
    session = get_object_or_404(Session, pk=session_id)
    
    if request.user not in [session.user1, session.user2]:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if not session.is_active:
        return JsonResponse({'error': 'Session ended'}, status=400)
    
    learner = session.user2 if request.user == session.user1 else session.user1
    if learner.credits < Decimal('1.00'):
        return JsonResponse({'error': 'Learner has insufficient credits (min 1 required).'}, status=400)
        
    timer = SessionTimer.start_timer(session, request.user)
    return JsonResponse({
        'success': True,
        'timer_id': timer.id,
        'teacher': request.user.name
    })


@login_required
@require_POST
def stop_timer(request, session_id):
    """Stop teaching timer."""
    session = get_object_or_404(Session, pk=session_id)
    
    active_timer = session.get_active_timer()
    if active_timer:
        active_timer.stop()
        return JsonResponse({
            'success': True,
            'duration': active_timer.duration_seconds
        })
    
    return JsonResponse({'error': 'No active timer'}, status=400)


@login_required
@require_POST
def end_session(request, session_id):
    """End session and calculate credits."""
    session = get_object_or_404(Session, pk=session_id)
    
    if request.user not in [session.user1, session.user2]:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if not session.is_active:
        return JsonResponse({'error': 'Session already ended'}, status=400)
    
    # End session and calculate credits
    session.end_session()
    credits = session.calculate_credits()
    
    bank = Bank.get_instance()
    
    # Apply credits
    if credits['user1_earned'] > 0:
        CreditTransaction.record_transaction(
            user=session.user1,
            amount=credits['user1_earned'],
            transaction_type='TEACHING',
            session=session,
            description=f'Teaching in session #{session.id}'
        )
    
    if credits['user2_earned'] > 0:
        CreditTransaction.record_transaction(
            user=session.user2,
            amount=credits['user2_earned'],
            transaction_type='TEACHING',
            session=session,
            description=f'Teaching in session #{session.id}'
        )
    
    if credits['user1_spent'] > 0:
        CreditTransaction.record_transaction(
            user=session.user1,
            amount=-credits['user1_spent'],
            transaction_type='LEARNING',
            session=session,
            description=f'Learning in session #{session.id}'
        )
    
    if credits['user2_spent'] > 0:
        CreditTransaction.record_transaction(
            user=session.user2,
            amount=-credits['user2_spent'],
            transaction_type='LEARNING',
            session=session,
            description=f'Learning in session #{session.id}'
        )
    
    # Bank cut
    if credits['bank_cut'] > 0:
        bank.add_credits(credits['bank_cut'])
        
    # Notify WebSocket
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'session_{session.id}',
        {
            'type': 'session_ended_message',
            'redirect_url': f'/session/{session.id}/review/'
        }
    )
    
    return JsonResponse({
        'success': True,
        'redirect': f'/session/{session_id}/review/'
    })


@login_required
def session_review(request, session_id):
    """Submit review after session ends."""
    session = get_object_or_404(Session, pk=session_id)
    
    if request.user not in [session.user1, session.user2]:
        messages.error(request, 'You are not part of this session.')
        return redirect('dashboard')
    
    partner = session.user2 if request.user == session.user1 else session.user1
    
    # Check if already reviewed
    existing_review = Review.objects.filter(session=session, reviewer=request.user).first()
    if existing_review:
        messages.info(request, 'You have already reviewed this session.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.session = session
            review.reviewer = request.user
            review.reviewee = partner
            review.save()
            messages.success(request, 'Review submitted successfully!')
            return redirect('dashboard')
    else:
        form = ReviewForm()
    
    return render(request, 'dashboard/review.html', {
        'session': session,
        'partner': partner,
        'form': form,
    })


@login_required
def my_sessions(request):
    """List user's sessions."""
    from django.db.models import Q
    sessions = Session.objects.filter(
        Q(user1=request.user) | Q(user2=request.user)
    ).select_related('user1', 'user2')[:20]
    
    return render(request, 'dashboard/sessions.html', {'sessions': sessions})


@login_required
def start_session(request, user_id):
    """Start a new session with another user."""
    other_user = get_object_or_404(User, pk=user_id)
    
    if other_user == request.user:
        messages.error(request, 'You cannot start a session with yourself.')
        return redirect('dashboard')
    
    # Check for existing active session
    from django.db.models import Q
    existing = Session.objects.filter(
        Q(user1=request.user, user2=other_user) | Q(user1=other_user, user2=request.user),
        is_active=True
    ).first()
    
    if existing:
        return redirect('session', session_id=existing.id)
    
    # Create new session
    session = Session.objects.create(user1=request.user, user2=other_user)
    messages.success(request, f'Session started with {other_user.name}!')
    return redirect('session', session_id=session.id)


@login_required
@require_POST
def save_session_state(request, session_id):
    """Save whiteboard and IDE state."""
    session = get_object_or_404(Session, pk=session_id)
    
    if request.user not in [session.user1, session.user2]:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    import json
    try:
        data = json.loads(request.body)
        fields_to_update = []
        
        if 'whiteboard' in data:
            session.whiteboard_state = data['whiteboard']
            fields_to_update.append('whiteboard_state')
            
        if 'ide_code' in data:
            session.ide_code = data['ide_code']
            fields_to_update.append('ide_code')
            
        if 'ide_language' in data:
            session.ide_language = data['ide_language']
            fields_to_update.append('ide_language')
            
        if fields_to_update:
            session.save(update_fields=fields_to_update)
            
        return JsonResponse({'success': True})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)


def users_list(request):
    """List all users (for discovery) with optional search."""
    users = User.objects.filter(is_active=True).exclude(pk=request.user.pk if request.user.is_authenticated else None)
    
    search = request.GET.get('search', '').strip()
    if search:
        users = users.filter(name__icontains=search)
        
    return render(request, 'profile/users_list.html', {'users': users, 'search': search})
