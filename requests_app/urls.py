"""
URL patterns for requests app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.all_requests, name='all_requests'),
    path('create/', views.create_request, name='create_request'),
    path('search-and-post/', views.search_and_post, name='search_and_post'),
    path('<int:request_id>/', views.request_detail, name='request_detail'),
    path('<int:request_id>/complete/', views.complete_request, name='complete_request'),
    path('<int:request_id>/delete/', views.delete_request, name='delete_request'),
]
