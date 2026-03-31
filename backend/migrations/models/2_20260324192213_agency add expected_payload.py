from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "connection_logs" (
    "id" UUID NOT NULL PRIMARY KEY,
    "action" VARCHAR(50) NOT NULL DEFAULT 'test',
    "connection_type" VARCHAR(20) NOT NULL,
    "status" VARCHAR(20) NOT NULL,
    "latency_ms" INT NOT NULL DEFAULT 0,
    "detail" TEXT NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "agency_id" UUID NOT NULL REFERENCES "agencies" ("id") ON DELETE CASCADE
);
        ALTER TABLE "agencies" ADD "expected_payload" JSONB;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "agencies" DROP COLUMN "expected_payload";
        DROP TABLE IF EXISTS "connection_logs";"""


MODELS_STATE = (
    "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"
    "Fy/z88sW0T"
)
