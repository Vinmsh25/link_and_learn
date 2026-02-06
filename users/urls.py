"""
URL patterns for users app.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Home & Auth
    path('', views.home, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('profile/<int:user_id>/', views.profile_view, name='user_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/credits/', views.credit_history, name='credit_history'),
    
    # Bank
    path('bank/', views.bank_view, name='bank'),
    
    # Users Discovery
    path('users/', views.users_list, name='users_list'),
    
    # Sessions
    path('sessions/', views.my_sessions, name='my_sessions'),
    path('session/<int:session_id>/', views.session_view, name='session'),
    path('session/<int:session_id>/start-timer/', views.start_timer, name='start_timer'),
    path('session/<int:session_id>/stop-timer/', views.stop_timer, name='stop_timer'),
    path('session/<int:session_id>/end/', views.end_session, name='end_session'),
    path('session/<int:session_id>/review/', views.session_review, name='session_review'),
    path('session/<int:session_id>/save-state/', views.save_session_state, name='save_session_state'),
    path('start-session/<int:user_id>/', views.start_session, name='start_session'),
]
