"""
Message routes — rating update.

Endpoints
---------
  PATCH  /messages/{id}/rating   Update message rating (up/down) + optional feedback
"""

import uuid

from fastapi import APIRouter, HTTPException
from tortoise.exceptions import DoesNotExist

from app.models.conversation import Message
from app.schemas.conversation import RatingUpdate

router = APIRouter(prefix="/messages", tags=["Messages"])


@router.patch("/{message_id}/rating", summary="Rate a message (up/down)")
async def update_rating(message_id: uuid.UUID, body: RatingUpdate) -> dict:
    try:
        msg = await Message.get(id=message_id)
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Message not found")

    msg.rating = body.rating
    if body.feedback_text is not None:
        msg.feedback_text = body.feedback_text

    update_fields = ["rating"]
    if body.feedback_text is not None:
        update_fields.append("feedback_text")

    await msg.save(update_fields=update_fields)
    return {"success": True, "messageId": str(message_id)}
