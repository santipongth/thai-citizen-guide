from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "user_api_keys" (
    "id" UUID NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "key" VARCHAR(255) NOT NULL UNIQUE,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "user_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
COMMENT ON TABLE "user_api_keys" IS 'API keys for users to access the AI Chatbot API.';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "user_api_keys";"""


MODELS_STATE = (
    "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"
    "9KX4Hg=="
)
