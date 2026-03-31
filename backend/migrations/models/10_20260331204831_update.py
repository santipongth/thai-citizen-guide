from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "connection_logs" ALTER COLUMN "agency_id" DROP NOT NULL;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "connection_logs" ALTER COLUMN "agency_id" SET NOT NULL;"""


MODELS_STATE = (
    "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"
    "9evv0PmSxebA=="
)
