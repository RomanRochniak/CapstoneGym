from django.contrib import admin
from .models import ChatSession, ChatMessage


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "is_active", "updated_at", "created_at")
    list_filter = ("is_active", "created_at", "updated_at")
    search_fields = ("id", "user__username", "user__email", "title")
    ordering = ("-updated_at",)
    raw_id_fields = ("user",)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "role", "short_content", "created_at")
    list_filter = ("role", "created_at")
    search_fields = ("content", "session__id", "session__user__username")
    ordering = ("-created_at",)
    raw_id_fields = ("session",)

    def short_content(self, obj: ChatMessage) -> str:
        text = obj.content or ""
        return (text[:80] + "…") if len(text) > 80 else text

    short_content.short_description = "content"