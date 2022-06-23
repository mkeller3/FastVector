from fastapi import FastAPI
import asyncpg

async def connect_to_db(app: FastAPI) -> None:
    """Connect."""
    app.state.data_pool = await asyncpg.create_pool(
        dsn="postgres://postgres:postgres@localhost:5432/data",
        min_size=1,
        max_size=10,
        max_queries=50000,
        max_inactive_connection_lifetime=300
    )

async def close_db_connection(app: FastAPI) -> None:
    """Close connection."""
    await app.state.data_pool.close()