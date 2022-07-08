from typing import Optional
import os
import shutil
from starlette.responses import FileResponse
from fastapi import Response, status, Request, APIRouter

router = APIRouter()

import utilities
import config

@router.get("/{database}/{scheme}/{table}/{z}/{x}/{y}.pbf", tags=["Tiles"])
async def tiles(database: str, scheme: str, table: str, z: int, x: int,
    y: int, request: Request,fields: Optional[str] = None, cql_filter: Optional[str] = None):
    """
    Method used to return a vector of tiles for a given table.
    """

    db_settings = config.DATABASES[database]

    pbf, tile_cache = await utilities.get_tile(
        database,
        scheme,
        table,
        z,
        x,
        y,
        fields,
        cql_filter,
        db_settings,
        request.app
    )

    response_code = status.HTTP_200_OK

    max_cache_age = db_settings['cache_age_in_seconds']

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

@router.get("/{database}/{scheme}/{table}.json", tags=["Tiles"])
async def tiles_json(database: str, scheme: str, table: str, request: Request):
    """
    Method used to return a tilejson information for a given table.
    """

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
        "version": "1.0.0",
        "scheme": "xyz",
        "tiles": [
            get_tile_url()
        ],
        "viewerurl": get_viewer_url(),
        "minzoom": 0,
        "maxzoom": 22,
    }

@router.get("/cache_size", tags=["Tiles"])
async def get_tile_cache_size():
    """
    Method used to a list of cache sizes for each table that has cache.
    """

    cache_sizes = []

    def get_size(start_path = '.'):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(start_path):
            for file in filenames:
                file_path = os.path.join(dirpath, file)
                if not os.path.islink(file_path):
                    total_size += os.path.getsize(file_path)

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

@router.delete("/cache", tags=["Tiles"])
async def delete_tile_cache(database: str, scheme: str, table: str):
    """
    Method used to delete cache for a table.
    """

    if os.path.exists(f'{os.getcwd()}/cache/{database}_{scheme}_{table}'):
        shutil.rmtree(f'{os.getcwd()}/cache/{database}_{scheme}_{table}')
        return {"status": "deleted"}
    else:
        return {"error": f"No cache at {os.getcwd()}/cache/{database}_{scheme}_{table}"}
