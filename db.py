from fastapi import FastAPI
import asyncpg
import config

async def connect_to_db(app: FastAPI) -> None:
    """Connect."""
    app.state.databases = {}
    for database in config.DATABASES:
        app.state.databases[f'{database}_pool'] = await asyncpg.create_pool(
            dsn=f"postgres://{config.DATABASES[database]['username']}:{config.DATABASES[database]['password']}@{config.DATABASES[database]['host']}:{config.DATABASES[database]['port']}/{database}",
            min_size=1,
            max_size=10,
            max_queries=50000,
            max_inactive_connection_lifetime=300
        )

async def close_db_connection(app: FastAPI) -> None:
    """Close connection."""
    for database in config.DATABASES:
        await app.state.databases[f'{database}_pool'].close()