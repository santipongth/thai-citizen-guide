from tortoise.models import Model
from tortoise import fields

class User(Model):
    id = fields.UUIDField(pk=True)
    email = fields.CharField(max_length=255, unique=True)
    hashed_password = fields.CharField(max_length=255)
    display_name = fields.CharField(max_length=50, null=True)
    is_admin = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True, index=True)
    updated_at = fields.DatetimeField(auto_now=True)

    def __str__(self):
        return self.display_name if self.display_name else self.email
