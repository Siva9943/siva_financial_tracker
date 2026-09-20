from django.urls import path

from .views import ChatView

chat_urlpatterns = [path('chat/', ChatView.as_view(), name='ai-chat')]
