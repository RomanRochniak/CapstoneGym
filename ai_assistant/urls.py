from django.urls import path
from .views import chat_api

urlpatterns = [
    path("api/ai/chat/", chat_api, name="ai_chat_api"),
]