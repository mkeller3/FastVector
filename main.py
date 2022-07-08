
"""FastVector App"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.templating import Jinja2Templates
from prometheus_fastapi_instrumentator import Instrumentator

from db import close_db_connection, connect_to_db
from routers import tiles, table


templates = Jinja2Templates(directory="templates")

DESCRIPTION = """
A lightweight python api to serve vector tiles from PostGIS.
"""

app = FastAPI(
    title="FastVector",
    description=DESCRIPTION,
    version="0.0.1",
    contact={
        "name": "Michael Keller",
        "email": "michaelkeller03@gmail.com",
    },
    license_info={
        "name": "The MIT License (MIT)",
        "url": "https://mit-license.org/",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    tiles.router,
    prefix="/api/v1/tiles",
    tags=["Tiles"],
)

app.include_router(
    table.router,
    prefix="/api/v1/table",
    tags=["Tables"],
)

Instrumentator().instrument(app).expose(app)


# Register Start/Stop application event handler to setup/stop the database connection
@app.on_event("startup")
async def startup_event():
    """Application startup: register the database connection and create table list."""
    await connect_to_db(app)


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown: de-register the database connection."""
    await close_db_connection(app)

@app.get("/api/v1/health_check", tags=["Health"])
async def health():
    """
    Method used to verify server is healthy.
    """

    return {"status": "UP"}

@app.get("/viewer/{database}/{scheme}/{table_name}", response_class=HTMLResponse, tags=["Viewer"])
async def viewer(request: Request, database: str, scheme: str, table_name: str):
    """
    Method used to to view a table in a web map.
    """

    return templates.TemplateResponse("viewer.html", {
        "request": request,
        "database": database,
        "scheme": scheme,
        "table": table_name
    })
