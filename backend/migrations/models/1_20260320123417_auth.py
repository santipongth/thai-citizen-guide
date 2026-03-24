from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "users" (
    "id" UUID NOT NULL PRIMARY KEY,
    "email" VARCHAR(255) NOT NULL UNIQUE,
    "display_name" VARCHAR(255),
    "hashed_password" VARCHAR(500) NOT NULL,
    "role" VARCHAR(20) NOT NULL DEFAULT 'user',
    "avatar_url" VARCHAR(500),
    "is_active" BOOL NOT NULL DEFAULT True,
    "reset_token" VARCHAR(255),
    "reset_token_expires" TIMESTAMPTZ,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE "users" IS 'Admin/user account for the AI Chatbot Portal.';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "users";"""


MODELS_STATE = (
    "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"
)
