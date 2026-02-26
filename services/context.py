from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from django.contrib.auth import get_user_model

from gym.models import Trainer, TrainingProgram, Membership


@dataclass(frozen=True)
class SiteContext:
    user: Dict[str, Any]
    membership: Optional[Dict[str, Any]]
    trainers: List[Dict[str, Any]]
    programs: List[Dict[str, Any]]


def build_site_context(user_id: int, limit: int = 30) -> SiteContext:
    User = get_user_model()
    user = User.objects.filter(id=user_id).first()

    user_payload = {
        "id": user.id if user else None,
        "username": user.username if user else None,
        "first_name": user.first_name if user else "",
        "last_name": user.last_name if user else "",
        "email": user.email if user else "",
        "is_authenticated": bool(user),
    }

    membership_obj = (
        Membership.objects
        .select_related("program", "program__trainer")
        .filter(user_id=user_id)
        .order_by("-end_date", "-start_date")
        .first()
    )

    membership_payload: Optional[Dict[str, Any]] = None
    if membership_obj:
        membership_payload = {
            "status": membership_obj.status,
            "start_date": membership_obj.start_date.isoformat(),
            "end_date": membership_obj.end_date.isoformat(),
            "program": {
                "id": membership_obj.program.id,
                "name": membership_obj.program.name,
                "price": str(membership_obj.program.price),
                "duration_min": membership_obj.program.duration,
                "trainer_id": membership_obj.program.trainer_id,
            },
            "trainer": {
                "id": membership_obj.program.trainer.id,
                "name": membership_obj.program.trainer.name,
                "specialization": membership_obj.program.trainer.specialization,
            } if membership_obj.program.trainer else None,
        }

    trainers_qs = Trainer.objects.all().order_by("id")[:limit]
    trainers_payload = [
        {
            "id": t.id,
            "name": t.name,
            "specialization": t.specialization,
            "description": (t.description or "")[:280],
        }
        for t in trainers_qs
    ]

    programs_qs = TrainingProgram.objects.select_related("trainer").all().order_by("id")[:limit]
    programs_payload = [
        {
            "id": p.id,
            "name": p.name,
            "description": (p.description or "")[:280],
            "duration_min": p.duration,
            "price": str(p.price),
            "trainer_id": p.trainer_id,
            "trainer_name": p.trainer.name if p.trainer else None,
        }
        for p in programs_qs
    ]

    return SiteContext(
        user=user_payload,
        membership=membership_payload,
        trainers=trainers_payload,
        programs=programs_payload,
    )


def detect_goal(text: str) -> Optional[str]:
    q = (text or "").lower()

    gain_kw = ["muscle", "bulk", "mass", "strength", "hypertrophy", "gain", "big"]
    loss_kw = ["lose", "loss", "cut", "fat", "lean", "weight loss", "calories"]
    endurance_kw = ["endurance", "cardio", "stamina", "run", "running", "conditioning", "fitness"]

    if any(k in q for k in gain_kw):
        return "muscle_gain"
    if any(k in q for k in loss_kw):
        return "weight_loss"
    if any(k in q for k in endurance_kw):
        return "endurance"
    return None


def match_trainers_and_programs(
    site: SiteContext,
    user_message: str,
    top_k: int = 3,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Optional[str]]:
    goal = detect_goal(user_message)
    if not goal:
        return [], [], None

    def score_trainer(t: Dict[str, Any]) -> int:
        s = (t.get("specialization") or "").lower()
        d = (t.get("description") or "").lower()
        hay = f"{s} {d}"

        if goal == "muscle_gain":
            keys = ["muscle", "mass", "strength", "gain", "hypertrophy", "bulk"]
        elif goal == "weight_loss":
            keys = ["fat", "loss", "cut", "lean", "weight", "cardio"]
        else:
            keys = ["endurance", "cardio", "fitness", "stamina", "conditioning", "run"]

        return sum(2 for k in keys if k in hay)

    def score_program(p: Dict[str, Any]) -> int:
        n = (p.get("name") or "").lower()
        d = (p.get("description") or "").lower()
        hay = f"{n} {d}"

        if goal == "muscle_gain":
            keys = ["mass", "muscle", "strength", "bulk", "hypertrophy"]
        elif goal == "weight_loss":
            keys = ["fat", "loss", "cut", "lean", "weight"]
        else:
            keys = ["endurance", "cardio", "fitness", "conditioning", "stamina"]

        return sum(2 for k in keys if k in hay)

    ranked_trainers = sorted(site.trainers, key=score_trainer, reverse=True)
    ranked_programs = sorted(site.programs, key=score_program, reverse=True)

    best_trainers = [t for t in ranked_trainers if score_trainer(t) > 0][:top_k]
    best_programs = [p for p in ranked_programs if score_program(p) > 0][:top_k]

    return best_trainers, best_programs, goal