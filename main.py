import shutil
import os
from typing import Optional
from fastapi import FastAPI, Response, status, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from starlette.templating import Jinja2Templates



from db import close_db_connection, connect_to_db
import utilities, config

templates = Jinja2Templates(directory="templates")

description = """
A lightweight python api to serve vector tiles from PostGIS.
"""

app = FastAPI(
    title="FastVector",
    description=description,
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


# Register Start/Stop application event handler to setup/stop the database connection
@app.on_event("startup")
async def startup_event():
    """Application startup: register the database connection and create table list."""
    await connect_to_db(app)


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown: de-register the database connection."""
    await close_db_connection(app)

@app.get("/api/v1/tiles/{database}/{scheme}/{table}/{z}/{x}/{y}.pbf", tags=["Tiles"])
async def tiles(database: str, scheme: str, table: str, z: int, x: int, y: int, fields: Optional[str] = None, cql_filter: Optional[str] = None):
    db_settings = config.DATABASES[database]

    pbf, tile_cache = await utilities.get_tile(database, scheme, table, z, x, y, fields, cql_filter, db_settings, app)

    response_code = status.HTTP_200_OK    

    max_cache_age = db_settings['cache']

    if fields is not None and cql_filter is not None:
        max_cache_age = 0

    if tile_cache:
        return FileResponse(
            path=f'{os.getcwd()}/cache/{database}_{scheme}_{table}/{z}/{x}/{y}',
            media_type="application/vnd.mapbox-vector-tile",
            status_code=response_code,
            headers = {
                "Cache-Control": f"max-age={max_cache_age}",
                "tile-cache": 'true'
            }
        )    

    if pbf == b"":
        response_code = status.HTTP_204_NO_CONTENT

    return Response(
        content=bytes(pbf),
        media_type="application/vnd.mapbox-vector-tile",
        status_code=response_code,
        headers = {
            "Cache-Control": f"max-age={max_cache_age}",
            "tile-cache": 'false'
        }
    )

@app.get("/api/v1/tile/{database}/{scheme}/{table}.json", tags=["Tiles"])
async def tiles_json(database: str, scheme: str, table: str, request: Request):
    def get_tile_url() -> str:
        """Return tile url for layer """
        url = str(request.base_url)
        url += f"api/v1/tiles/{database}/{scheme}/{table}"
        url += "/{z}/{x}/{y}.pbf"
        return url
    
    def get_viewer_url() -> str:
        """Return viewer url for layer """
        url = str(request.base_url)
        url += f"viewer/{database}/{scheme}/{table}"
        return url

    return {
        "tilejson": "2.2.0",
        "name": f"{scheme}.{table}",
        # "description": "A simple, light grey world.",
        "version": "1.0.0",
        # "attribution": "<a href='http://openstreetmap.org'>OSM contributors</a>",
        # "legend": "Dangerous zones are red, safe zones are green",
        "scheme": "xyz",
        "tiles": [
            get_tile_url()
        ],
        "viewerurl": get_viewer_url(),
        # "grids": [
        #     "http://localhost:8888/admin/1.0.0/broadband/{z}/{x}/{y}.grid.json"
        # ],
        # "data": [
        #     "http://localhost:8888/admin/data.geojson"
        # ],
        "minzoom": 0,
        "maxzoom": 22,
        # "bounds": [ -180, -85.05112877980659, 180, 85.0511287798066 ],
        # "center": [ -76.275329586789, 39.153492567373, 8 ]
    }

@app.get("/api/v1/tables.json", tags=["Tables"])
async def tables(request: Request):
    def get_detail_url(table: object) -> str:
        """Return tile url for layer """
        url = str(request.base_url)
        url += f"api/v1/table/{table['database']}/{table['schema']}/{table['name']}.json"
        return url
    def get_viewer_url(table: object) -> str:
        """Return tile url for layer """
        url = str(request.base_url)
        url += f"viewer/{table['database']}/{table['schema']}/{table['name']}"
        return url
    tables = await utilities.get_tables_metadata(app)
    for table in tables:
        table['detailurl'] = get_detail_url(table)
        table['viewerurl'] = get_viewer_url(table)
    return tables

@app.get("/api/v1/table/{database}/{scheme}/{table}.json", tags=["Tables"])
async def table_json(database: str, scheme: str, table: str, request: Request):
    def get_tile_url() -> str:
        """Return tile url for layer """
        url = str(request.base_url)
        url += f"api/v1/tiles/{database}/{scheme}/{table}"
        url += "/{z}/{x}/{y}.pbf"
        return url
    
    def get_viewer_url() -> str:
        """Return viewer url for layer """
        url = str(request.base_url)
        url += f"viewer/{database}/{scheme}/{table}"
        return url

    return {
        "id": f"{scheme}.{table}",
        "schema": scheme,
        "tileurl": get_tile_url(),
        "viewerurl": get_viewer_url(),
        "properties": await utilities.get_table_columns(database, scheme, table, app),
        "geometrytype": await utilities.get_table_geometry_type(database, scheme, table, app),
        "type": "table",
        "minzoom": 0,
        "maxzoom": 22,
        "bounds": await utilities.get_table_bounds(database, scheme, table, app),
        "center": await utilities.get_table_center(database, scheme, table, app)
    }

@app.get("/api/v1/cache_size", tags=["Cache"])
async def cache_size():
    cache_sizes = []
    def get_size(start_path = '.'):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(start_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)

        return total_size
    cache_folders = os.listdir(f'{os.getcwd()}/cache/')

    for folder in cache_folders:
        cache_sizes.append(
            {
                "table": folder,
                "size_in_gigabytes": get_size(f'{os.getcwd()}/cache/{folder}')*.000000001
            }
        )

    return cache_sizes

@app.delete("/api/v1/cache", tags=["Cache"])
async def delete_cache(database: str, scheme: str, table: str):
    if os.path.exists(f'{os.getcwd()}/cache/{database}_{scheme}_{table}'):
        shutil.rmtree(f'{os.getcwd()}/cache/{database}_{scheme}_{table}')
        return {"status": "deleted"}
    else:
        return {"error": f"No cache at {os.getcwd()}/cache/{database}_{scheme}_{table}"}

@app.get("/api/v1/health_check", tags=["Health"])
async def health():
    return {"status": "UP"}

@app.get("/viewer/{database}/{scheme}/{table}", response_class=HTMLResponse, tags=["Viewer"])
async def viewer(request: Request, database: str, scheme: str, table: str):
    return templates.TemplateResponse("viewer.html", {"request": request, "database": database, "scheme": scheme, "table": table})

# @app.get("/", response_class=HTMLResponse, tags=["Home"])
# async def viewer(request: Request):
#     def get_detail_url(table: object) -> str:
#         """Return tile url for layer """
#         url = str(request.base_url)
#         url += f"api/v1/table/{table['database']}/{table['schema']}/{table['name']}.json"
#         return url
#     def get_viewer_url(table: object) -> str:
#         """Return tile url for layer """
#         url = str(request.base_url)
#         url += f"viewer/{table['database']}/{table['schema']}/{table['name']}"
#         return url
#     tables = await utilities.get_tables_metadata(app)
#     for table in tables:
#         table['detailurl'] = get_detail_url(table)
#         table['viewerurl'] = get_viewer_url(table)
#     return templates.TemplateResponse("index.html", {"request": request, "tables": tables})
