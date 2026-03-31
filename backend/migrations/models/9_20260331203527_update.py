from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "messages" ADD "errors" JSONB;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "messages" DROP COLUMN "errors";"""


MODELS_STATE = (
    "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"
    "yQneW5lDA6dr+9vPwfvoFfTQ=="
)
