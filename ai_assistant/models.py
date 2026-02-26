from __future__ import annotations

from django.conf import settings
from django.db import models


class ChatSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_chat_sessions",
    )
    title = models.CharField(max_length=120, blank=True, default="")
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "is_active", "-updated_at"]),
        ]
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"ChatSession(id={self.id}, user_id={self.user_id})"


class ChatMessage(models.Model):
    ROLE_SYSTEM = "system"
    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"

    ROLE_CHOICES = (
        (ROLE_SYSTEM, "System"),
        (ROLE_USER, "User"),
        (ROLE_ASSISTANT, "Assistant"),
    )

    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=12, choices=ROLE_CHOICES)
    content = models.TextField()

    meta = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["session", "created_at"]),
            models.Index(fields=["session", "role", "created_at"]),
        ]
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"ChatMessage(id={self.id}, role={self.role}, session_id={self.session_id})"