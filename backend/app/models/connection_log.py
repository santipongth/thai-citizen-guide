"""
ConnectionLog — records every agency connection test or query attempt.
"""

import uuid

from tortoise import fields, models


class ConnectionLog(models.Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    agency: fields.ForeignKeyRelation = fields.ForeignKeyField(
        "models.Agency",
        related_name="connection_logs",
        on_delete=fields.CASCADE,
    )
    action = fields.CharField(max_length=50, default="test")   # test | query
    connection_type = fields.CharField(max_length=20)          # MCP | API | A2A
    status = fields.CharField(max_length=20)                   # success | error
    latency_ms = fields.IntField(default=0)
    detail = fields.TextField(default="")
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "connection_logs"
        ordering = ["-created_at"]
