from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "messages" ADD "category" VARCHAR(50);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "messages" DROP COLUMN "category";"""


MODELS_STATE = (
    "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"
)
