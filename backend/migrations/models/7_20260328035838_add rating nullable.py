from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "agencies" ADD "rating_down" INT NOT NULL DEFAULT 0;
        ALTER TABLE "agencies" ADD "rating_up" INT NOT NULL DEFAULT 0;
        ALTER TABLE "messages" ADD "agency_ids" JSONB;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "agencies" DROP COLUMN "rating_down";
        ALTER TABLE "agencies" DROP COLUMN "rating_up";
        ALTER TABLE "messages" DROP COLUMN "agency_ids";"""


MODELS_STATE = (
    "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"
    "nJ3/kp1/vLM8zdIikK3luRRwOra/vDz9Dx8LdMQ="
)
