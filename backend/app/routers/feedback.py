"""
Feedback stats route — port of the Supabase `feedback-stats` edge function.

Endpoint
--------
  GET  /feedback/stats
"""

from datetime import datetime, timedelta

from fastapi import APIRouter
from tortoise.functions import Count

from app.models.conversation import Conversation, Message
from app.schemas.conversation import FeedbackStats

router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.get("/stats", response_model=FeedbackStats, summary="Get feedback and satisfaction metrics")
async def feedback_stats() -> FeedbackStats:
    # All rated messages, newest first
    rated_messages = await (
        Message.filter(rating__not_isnull=True)
        .order_by("-created_at")
        .values("id", "rating", "feedback_text", "content", "created_at", "conversation_id")
    )

    up_count = sum(1 for m in rated_messages if m["rating"] == "up")
    down_count = sum(1 for m in rated_messages if m["rating"] == "down")
    total_ratings = up_count + down_count
    satisfaction_rate = round((up_count / total_ratings) * 100) if total_ratings > 0 else 0

    # -------------------------------------------------------------------
    # Daily trend — last 14 days
    # -------------------------------------------------------------------
    now = datetime.utcnow()
    daily_map: dict[str, dict] = {}
    for i in range(13, -1, -1):
        key = (now - timedelta(days=i)).strftime("%m-%d")
        daily_map[key] = {"up": 0, "down": 0}

    for m in rated_messages:
        if m["created_at"]:
            day_key = m["created_at"].strftime("%m-%d")
            if day_key in daily_map:
                if m["rating"] == "up":
                    daily_map[day_key]["up"] += 1
                elif m["rating"] == "down":
                    daily_map[day_key]["down"] += 1

    daily_trend = [
        {
            "date": k,
            "up": v["up"],
            "down": v["down"],
            "rate": round((v["up"] / (v["up"] + v["down"])) * 100) if (v["up"] + v["down"]) > 0 else 0,
        }
        for k, v in daily_map.items()
    ]

    # -------------------------------------------------------------------
    # Low-rated questions (last 10 down-rated assistant messages)
    # -------------------------------------------------------------------
    down_rated = [m for m in rated_messages if m["rating"] == "down"][:10]
    low_rated_questions = []

    for dr in down_rated:
        # Get most recent user message from same conversation
        user_msg = await (
            Message.filter(conversation_id=dr["conversation_id"], role="user")
            .order_by("-created_at")
            .first()
        )
        conv = await Conversation.filter(id=dr["conversation_id"]).first()

        low_rated_questions.append({
            "content": user_msg.content if user_msg else "ไม่ทราบคำถาม",
            "feedback_text": dr.get("feedback_text"),
            "agency": ", ".join(conv.agencies) if conv and conv.agencies else "-",
            "created_at": dr["created_at"].isoformat() if dr.get("created_at") else "",
        })

    # -------------------------------------------------------------------
    # Agency breakdown
    # -------------------------------------------------------------------
    agency_map: dict[str, dict] = {}
    conv_ids = list({m["conversation_id"] for m in rated_messages})

    if conv_ids:
        convs = await Conversation.filter(id__in=conv_ids).values("id", "agencies")
        conv_agency_map = {str(c["id"]): c["agencies"] or [] for c in convs}

        for m in rated_messages:
            conv_id = str(m["conversation_id"])
            for ag in conv_agency_map.get(conv_id, []):
                if ag not in agency_map:
                    agency_map[ag] = {"up": 0, "down": 0}
                if m["rating"] == "up":
                    agency_map[ag]["up"] += 1
                else:
                    agency_map[ag]["down"] += 1

    agency_breakdown = sorted(
        [
            {
                "agency": ag,
                "up": v["up"],
                "down": v["down"],
                "rate": round((v["up"] / (v["up"] + v["down"])) * 100) if (v["up"] + v["down"]) > 0 else 0,
            }
            for ag, v in agency_map.items()
        ],
        key=lambda x: x["up"] + x["down"],
        reverse=True,
    )

    return FeedbackStats(
        total_ratings=total_ratings,
        up_count=up_count,
        down_count=down_count,
        satisfaction_rate=satisfaction_rate,
        daily_trend=daily_trend,
        low_rated_questions=low_rated_questions,
        agency_breakdown=agency_breakdown,
    )
