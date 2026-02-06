"""
URL configuration for Link & Learn project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('requests/', include('requests_app.urls')),
    path('chat/', include('chat.urls')),
    path('skills/', include('skills.urls')),
]
