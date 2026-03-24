import uuid

from tortoise import fields
from tortoise.models import Model


class Conversation(Model):
    """
    Chat conversation — mirrors the `conversations` table from the original Supabase schema.
    """

    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    title = fields.CharField(max_length=500, default="สนทนาใหม่")
    preview = fields.TextField(null=True)
    agencies = fields.JSONField(default=list)          # list[str] — agency names used
    status = fields.CharField(max_length=20, default="success")   # success | failed
    message_count = fields.IntField(default=0)
    response_time = fields.CharField(max_length=50, null=True)

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    user = fields.ForeignKeyField(
        "models.User",
        related_name="conversations",
        on_delete=fields.SET_NULL,
        null=True,
    )

    class Meta:
        table = "conversations"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title


class Message(Model):
    """
    Individual chat message within a conversation.
    """

    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    conversation = fields.ForeignKeyField(
        "models.Conversation",
        related_name="messages",
        on_delete=fields.CASCADE,
    )
    role = fields.CharField(max_length=20)              # user | assistant
    content = fields.TextField()
    agent_steps = fields.JSONField(default=list)        # list of AgentStep objects
    sources = fields.JSONField(default=list)            # list of source references
    rating = fields.CharField(max_length=10, null=True) # up | down | None
    feedback_text = fields.TextField(null=True)

    created_at = fields.DatetimeField(auto_now_add=True)
    
    user = fields.ForeignKeyField(
        "models.User",
        related_name="messages",
        on_delete=fields.SET_NULL,
        null=True,
    )

    class Meta:
        table = "messages"
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"[{self.role}] {self.content[:60]}"
