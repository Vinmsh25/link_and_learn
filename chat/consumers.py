"""
WebSocket consumers for real-time chat.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model


class SessionChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for session chat."""
    
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'session_{self.session_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'chat')
        
        if message_type == 'chat':
            await self.handle_chat_message(data)
        elif message_type == 'timer':
            await self.handle_timer_event(data)
        elif message_type == 'whiteboard':
            await self.handle_whiteboard_event(data)
        elif message_type == 'code_change':
            await self.handle_code_change(data)
        elif message_type == 'video_signal':
            await self.handle_video_signal(data)
    
    async def handle_chat_message(self, data):
        content = data.get('content', '')
        user = self.scope['user']
        
        if user.is_authenticated and content:
            # Save message to database
            await self.save_message(content)
            
            # Broadcast to room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'sender': user.name,
                    'sender_id': user.id,
                    'content': content,
                }
            )
    
    async def handle_timer_event(self, data):
        user = self.scope['user']
        action = data.get('action')  # 'start', 'stop'
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'timer_update',
                'action': action,
                'user_id': user.id,
                'user_name': user.name,
            }
        )
    
    async def handle_whiteboard_event(self, data):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'whiteboard_update',
                'data': data.get('data'),
                'sender_channel_name': self.channel_name
            }
        )

    async def handle_code_change(self, data):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'code_update',
                'code': data.get('code'),
                'language': data.get('language'),
                'sender_channel_name': self.channel_name
            }
        )

    async def handle_video_signal(self, data):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'video_signal_message',
                'data': data.get('data'),
                'sender_channel_name': self.channel_name
            }
        )
    
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat',
            'sender': event['sender'],
            'sender_id': event['sender_id'],
            'content': event['content'],
        }))
    
    async def timer_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'timer',
            'action': event['action'],
            'user_id': event['user_id'],
            'user_name': event['user_name'],
        }))
    
    async def whiteboard_update(self, event):
        if event.get('sender_channel_name') == self.channel_name:
            return
            
        await self.send(text_data=json.dumps({
            'type': 'whiteboard',
            'data': event['data'],
        }))

    async def code_update(self, event):
        if event.get('sender_channel_name') == self.channel_name:
            return

        await self.send(text_data=json.dumps({
            'type': 'code_change',
            'code': event['code'],
            'language': event.get('language'),
        }))

    async def video_signal_message(self, event):
        if event.get('sender_channel_name') == self.channel_name:
            return

        await self.send(text_data=json.dumps({
            'type': 'video_signal',
            'data': event['data'],
        }))

    async def session_ended_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'session_ended',
            'redirect_url': event['redirect_url']
        }))
    
    @database_sync_to_async
    def save_message(self, content):
        from chat.models import ChatMessage
        from users.models import Session
        
        try:
            session = Session.objects.get(pk=self.session_id)
            ChatMessage.objects.create(
                session=session,
                sender=self.scope['user'],
                content=content
            )
        except Session.DoesNotExist:
            pass
