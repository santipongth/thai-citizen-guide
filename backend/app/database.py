from tortoise import Tortoise
from app.config import TORTOISE_ORM


async def init_db() -> None:
    """Initialize Tortoise ORM and generate schemas."""
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas(safe=True)


async def close_db() -> None:
    """Close all Tortoise ORM connections."""
    await Tortoise.close_connections()
