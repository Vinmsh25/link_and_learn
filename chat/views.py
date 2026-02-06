"""
Chat views.
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model

from .models import ChatMessage, DirectMessage
from users.models import Session

User = get_user_model()


@login_required
def session_chat(request, session_id):
    """Get chat messages for a session."""
    session = get_object_or_404(Session, pk=session_id)
    
    if request.user not in [session.user1, session.user2]:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    messages = ChatMessage.objects.filter(session=session).select_related('sender')
    
    return JsonResponse({
        'messages': [
            {
                'id': msg.id,
                'sender': msg.sender.name,
                'sender_id': msg.sender.id,
                'content': msg.content,
                'timestamp': msg.created_at.isoformat(),
            }
            for msg in messages
        ]
    })


@login_required
@require_POST
def send_message(request, session_id):
    """Send a message in a session."""
    session = get_object_or_404(Session, pk=session_id)
    
    if request.user not in [session.user1, session.user2]:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'error': 'Empty message'}, status=400)
    
    msg = ChatMessage.objects.create(
        session=session,
        sender=request.user,
        content=content
    )
    
    return JsonResponse({
        'success': True,
        'message': {
            'id': msg.id,
            'sender': msg.sender.name,
            'sender_id': msg.sender.id,
            'content': msg.content,
            'timestamp': msg.created_at.isoformat(),
        }
    })


@login_required
def direct_chat(request, user_id):
    """Direct chat page with another user."""
    other_user = get_object_or_404(User, pk=user_id)
    
    from django.db.models import Q
    messages = DirectMessage.objects.filter(
        Q(sender=request.user, receiver=other_user) |
        Q(sender=other_user, receiver=request.user)
    ).select_related('sender', 'receiver')
    
    # Mark messages as read
    DirectMessage.objects.filter(
        sender=other_user, receiver=request.user, is_read=False
    ).update(is_read=True)
    
    return render(request, 'chat/direct.html', {
        'other_user': other_user,
        'messages': messages,
    })


@login_required
@require_POST
def send_direct_message(request, user_id):
    """Send a direct message to another user."""
    other_user = get_object_or_404(User, pk=user_id)
    
    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'error': 'Empty message'}, status=400)
    
    msg = DirectMessage.objects.create(
        sender=request.user,
        receiver=other_user,
        content=content
    )
    
    return JsonResponse({
        'success': True,
        'message': {
            'id': msg.id,
            'sender': msg.sender.name,
            'content': msg.content,
            'timestamp': msg.created_at.isoformat(),
        }
    })


@login_required
def get_direct_messages(request, user_id):
    """Get direct messages with a user (AJAX polling)."""
    other_user = get_object_or_404(User, pk=user_id)
    
    from django.db.models import Q
    messages = DirectMessage.objects.filter(
        Q(sender=request.user, receiver=other_user) |
        Q(sender=other_user, receiver=request.user)
    ).select_related('sender')
    
    return JsonResponse({
        'messages': [
            {
                'id': msg.id,
                'sender': msg.sender.name,
                'sender_id': msg.sender.id,
                'content': msg.content,
                'timestamp': msg.created_at.isoformat(),
                'is_mine': msg.sender == request.user,
            }
            for msg in messages
        ]
    })
