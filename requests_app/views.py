"""
Learning Request views.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.views.decorators.http import require_POST

from .models import LearningRequest
from .forms import LearningRequestForm


@login_required
def create_request(request):
    """Create a new learning request (search)."""
    if request.method == 'POST':
        form = LearningRequestForm(request.POST)
        if form.is_valid():
            learning_request = form.save(commit=False)
            learning_request.creator = request.user
            learning_request.save()
            messages.success(request, 'Learning request posted!')
            return redirect('all_requests')
    else:
        form = LearningRequestForm()
    
    return render(request, 'dashboard/create_request.html', {'form': form})


@login_required
def all_requests(request):
    """List all learning requests with optional filtering."""
    requests_qs = LearningRequest.get_active_requests().select_related('creator')
    
    # Search filters
    search = request.GET.get('search', '').strip()
    teach_search = request.GET.get('teach', '').strip()
    bounty_only = request.GET.get('bounty') == '1'
    
    found_users = None
    is_search = False
    
    if search or teach_search:
        is_search = True
        # Search mode: Find relevant profiles
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        users_qs = User.objects.filter(is_active=True).exclude(pk=request.user.pk)
        
        if search:
            # Search by name or what they want to learn/teach
            users_qs = users_qs.filter(
                Q(name__icontains=search) |
                Q(learning_requests__topic_to_learn__icontains=search) |
                Q(learning_requests__topic_to_teach__icontains=search)
            ).distinct()
            
        if teach_search:
            # Filter by what they can teach
            users_qs = users_qs.filter(
                learning_requests__topic_to_teach__icontains=teach_search
            ).distinct()
            
        found_users = users_qs
    else:
        # Browse mode: Show all others' posts
        requests_qs = requests_qs.exclude(creator=request.user)
        if bounty_only:
             requests_qs = requests_qs.filter(ok_with_just_learning=True)
    
    return render(request, 'dashboard/all_requests.html', {
        'requests': requests_qs if not is_search else None,
        'found_users': found_users,
        'is_search': is_search,
        'search': search,
        'teach_search': teach_search,
        'bounty_only': bounty_only,
    })


@login_required
@require_POST
def search_and_post(request):
    """Create a request from search inputs and show matches."""
    topic_to_learn = request.POST.get('topic_to_learn', '').strip()
    topic_to_teach = request.POST.get('topic_to_teach', '').strip()
    ok_with_just_learning = request.POST.get('ok_with_just_learning') == 'true'
    
    if not topic_to_learn:
        messages.error(request, 'Please specify what you want to learn.')
        return redirect('all_requests')
        
    # Create request
    LearningRequest.objects.create(
        creator=request.user,
        topic_to_learn=topic_to_learn,
        topic_to_teach=topic_to_teach,
        ok_with_just_learning=ok_with_just_learning
    )
    
    messages.success(request, f'Request posted! Showing matches for "{topic_to_learn}".')
    
    # Redirect to search results
    url = f"/requests/?search={topic_to_learn}"
    if topic_to_teach:
        url += f"&teach={topic_to_teach}"
        
    return redirect(url)


@login_required
def request_detail(request, request_id):
    """View a single learning request."""
    learning_request = get_object_or_404(LearningRequest, pk=request_id)
    
    return render(request, 'dashboard/request_detail.html', {
        'learning_request': learning_request,
    })


@login_required
def complete_request(request, request_id):
    """Mark a request as completed."""
    learning_request = get_object_or_404(LearningRequest, pk=request_id, creator=request.user)
    learning_request.mark_completed()
    messages.success(request, 'Request marked as completed!')
    return redirect('dashboard')


@login_required
def delete_request(request, request_id):
    """Delete a learning request."""
    learning_request = get_object_or_404(LearningRequest, pk=request_id, creator=request.user)
    learning_request.delete()
    messages.success(request, 'Request deleted.')
    return redirect('dashboard')
