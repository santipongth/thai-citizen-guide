from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "conversations" ADD "external_session_id" VARCHAR(100);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "conversations" DROP COLUMN "external_session_id";"""


MODELS_STATE = (
    "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"
    "rm+g=="
)
