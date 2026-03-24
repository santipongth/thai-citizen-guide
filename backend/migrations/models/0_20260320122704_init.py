from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "agencies" (
    "id" UUID NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "short_name" VARCHAR(50),
    "logo" VARCHAR(20),
    "description" TEXT,
    "connection_type" VARCHAR(10) NOT NULL DEFAULT 'API',
    "status" VARCHAR(20) NOT NULL DEFAULT 'active',
    "data_scope" JSONB NOT NULL,
    "color" VARCHAR(50),
    "endpoint_url" VARCHAR(1000),
    "auth_method" VARCHAR(50),
    "auth_header" VARCHAR(100),
    "base_path" VARCHAR(255),
    "api_key_name" VARCHAR(100),
    "rate_limit_rpm" INT,
    "request_format" VARCHAR(50),
    "api_endpoints" JSONB NOT NULL,
    "response_schema" JSONB NOT NULL,
    "api_spec_raw" TEXT,
    "total_calls" INT NOT NULL DEFAULT 0,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON COLUMN "agencies"."connection_type" IS 'MCP: MCP\nAPI: API\nA2A: A2A';
COMMENT ON COLUMN "agencies"."status" IS 'active: active\ninactive: inactive';
COMMENT ON TABLE "agencies" IS 'Government agency model.';
CREATE TABLE IF NOT EXISTS "conversations" (
    "id" UUID NOT NULL PRIMARY KEY,
    "title" VARCHAR(500) NOT NULL DEFAULT 'สนทนาใหม่',
    "preview" TEXT,
    "agencies" JSONB NOT NULL,
    "status" VARCHAR(20) NOT NULL DEFAULT 'success',
    "message_count" INT NOT NULL DEFAULT 0,
    "response_time" VARCHAR(50),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE "conversations" IS 'Chat conversation — mirrors the `conversations` table from the original Supabase schema.';
CREATE TABLE IF NOT EXISTS "messages" (
    "id" UUID NOT NULL PRIMARY KEY,
    "role" VARCHAR(20) NOT NULL,
    "content" TEXT NOT NULL,
    "agent_steps" JSONB NOT NULL,
    "sources" JSONB NOT NULL,
    "rating" VARCHAR(10),
    "feedback_text" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "conversation_id" UUID NOT NULL REFERENCES "conversations" ("id") ON DELETE CASCADE
);
COMMENT ON TABLE "messages" IS 'Individual chat message within a conversation.';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
    "3nmcZw=="
)
