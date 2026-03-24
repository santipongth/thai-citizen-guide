from tortoise import Tortoise
from app.config import TORTOISE_ORM
from aerich import Command
from aerich.utils import load_tortoise_config

async def init_db() -> None:
    """Initialize Tortoise ORM and generate schemas."""
    
    async with Command(tortoise_config=TORTOISE_ORM) as command:
        await command.upgrade()

    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas(safe=True)


async def close_db() -> None:
    """Close all Tortoise ORM connections."""
    await Tortoise.close_connections()