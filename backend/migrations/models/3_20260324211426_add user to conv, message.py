from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "conversations" ADD "user_id" UUID;
        ALTER TABLE "messages" ADD "user_id" UUID;
        ALTER TABLE "conversations" ADD CONSTRAINT "fk_conversa_users_3da93cbc" FOREIGN KEY ("user_id") REFERENCES "users" ("id") ON DELETE SET NULL;
        ALTER TABLE "messages" ADD CONSTRAINT "fk_messages_users_3b8fb3a8" FOREIGN KEY ("user_id") REFERENCES "users" ("id") ON DELETE SET NULL;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "conversations" DROP CONSTRAINT IF EXISTS "fk_conversa_users_3da93cbc";
        ALTER TABLE "messages" DROP CONSTRAINT IF EXISTS "fk_messages_users_3b8fb3a8";
        ALTER TABLE "messages" DROP COLUMN "user_id";
        ALTER TABLE "conversations" DROP COLUMN "user_id";"""


MODELS_STATE = (
    "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"
)
