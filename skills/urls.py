from django.urls import path
from . import views

urlpatterns = [
    path('', views.skills_list, name='skills_list'),
]
