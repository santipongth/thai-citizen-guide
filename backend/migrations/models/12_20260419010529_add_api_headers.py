from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "agencies" ADD "api_headers" JSONB;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "agencies" DROP COLUMN "api_headers";"""


MODELS_STATE = (
    "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"
    "bRvt1rK/K1Bx299efvwNGv90IQ=="
)
