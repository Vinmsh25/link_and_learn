from django.urls import path
from . import views

urlpatterns = [
    path('session/<int:session_id>/', views.session_chat, name='session_chat'),
    path('session/<int:session_id>/send/', views.send_message, name='send_session_message'),
    path('direct/<int:user_id>/', views.direct_chat, name='direct_chat'),
    path('direct/<int:user_id>/send/', views.send_direct_message, name='send_direct_message'),
    path('direct/<int:user_id>/messages/', views.get_direct_messages, name='get_direct_messages'),
]
