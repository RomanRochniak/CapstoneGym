import json
import logging
from typing import Dict, List, Optional

import httpx
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import ChatMessage, ChatSession
from services.ai_service import LLMService
from services.context import build_site_context, match_trainers_and_programs

logger = logging.getLogger(__name__)


def _rate_key(user_id: int) -> str:
    return f"ai:rl:{user_id}"


def _allow_request(user_id: int) -> bool:
    limit = getattr(settings, "AI_RATE_LIMIT_PER_MIN", 12)
    key = _rate_key(user_id)
    current = cache.get(key, 0)

    if current >= limit:
        return False

    cache.set(key, current + 1, timeout=60)
    return True


def _get_history(session: ChatSession, limit: int = 10) -> List[Dict[str, str]]:
    qs = session.messages.exclude(role=ChatMessage.ROLE_SYSTEM).order_by("-created_at")[:limit]
    msgs = list(reversed(qs))
    return [{"role": m.role, "content": m.content} for m in msgs]


@login_required
@require_POST
def chat_api(request):
    if not _allow_request(request.user.id):
        return JsonResponse({"error": "Rate limit exceeded. Please slow down."}, status=429)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    message = (payload.get("message") or "").strip()
    session_id = payload.get("session_id")

    if not message:
        return JsonResponse({"error": "Message is required"}, status=400)

    session: Optional[ChatSession] = None

    if session_id:
        session = ChatSession.objects.filter(
            id=session_id,
            user=request.user,
            is_active=True,
        ).first()
        if not session:
            return JsonResponse({"error": "Session not found"}, status=404)
    else:
        session = ChatSession.objects.create(user=request.user, title="")

    ChatMessage.objects.create(
        session=session,
        role=ChatMessage.ROLE_USER,
        content=message,
    )

    history = _get_history(session, limit=10)

    site = build_site_context(request.user.id)
    best_trainers, best_programs, goal = match_trainers_and_programs(site, message, top_k=3)

    suggestions = {
        "goal_detected": goal,
        "recommended_trainers": best_trainers,
        "recommended_programs": best_programs,
        "membership": site.membership,
    }

    service = LLMService()

    try:
        resp = service.generate_response(
            user_message=message,
            conversation_history=history[:-1],
            site_context={
                "trainers": site.trainers,
                "programs": site.programs,
                "membership": site.membership,
            },
            suggestions=suggestions,
        )
    except httpx.TimeoutException:
        logger.exception("AI timeout")
        return JsonResponse(
            {"error": "AI timeout. Please try again in a few seconds."},
            status=504,
        )
    except httpx.HTTPStatusError as e:
        status_code = e.response.status_code
        body = e.response.text[:2000]

        logger.exception(
            "AI upstream HTTP error status=%s body=%s",
            status_code,
            body,
        )

        if status_code == 429:
            return JsonResponse(
                {"error": f"Gemini quota/rate limit exceeded. Details: {body}"},
                status=429,
            )

        if status_code == 400:
            return JsonResponse(
                {"error": f"Gemini request rejected. Details: {body}"},
                status=502,
            )

        if status_code == 401:
            return JsonResponse(
                {"error": f"Gemini authentication failed. Details: {body}"},
                status=502,
            )

        if status_code == 403:
            return JsonResponse(
                {"error": f"Gemini access denied. Details: {body}"},
                status=502,
            )

        if status_code == 404:
            return JsonResponse(
                {"error": f"Gemini model or endpoint not found. Details: {body}"},
                status=502,
            )

        if status_code >= 500:
            return JsonResponse(
                {"error": f"Gemini upstream server error ({status_code}). Details: {body}"},
                status=502,
            )

        return JsonResponse(
            {"error": f"AI upstream service failed ({status_code}). Details: {body}"},
            status=502,
        )
    except Exception as e:
        logger.exception("AI chat failed: %s", str(e))
        return JsonResponse(
            {"error": f"AI internal error: {str(e)}"},
            status=500,
        )

    ChatMessage.objects.create(
        session=session,
        role=ChatMessage.ROLE_ASSISTANT,
        content=resp.text,
        meta={
            "provider": resp.provider,
            "model": resp.model,
            **(resp.meta or {}),
        },
    )

    return JsonResponse(
        {
            "session_id": session.id,
            "response": resp.text,
            "provider": resp.provider,
            "model": resp.model,
            "suggestions": suggestions,
        }
    )