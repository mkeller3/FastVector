from fastapi import Request, APIRouter

import utilities

router = APIRouter()


@router.get("/tables.json", tags=["Tables"])
async def tables(request: Request):
    """
    Method used to return a list of tables available to query for vector tiles.
    """

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
    db_tables = await utilities.get_tables_metadata(request.app)
    for table in db_tables:
        table['detailurl'] = get_detail_url(table)
        table['viewerurl'] = get_viewer_url(table)

    return db_tables

@router.get("/{database}/{scheme}/{table}.json", tags=["Tables"])
async def table_json(database: str, scheme: str, table: str, request: Request):
    """
    Method used to return a information for a given table.
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
        "id": f"{scheme}.{table}",
        "schema": scheme,
        "tileurl": get_tile_url(),
        "viewerurl": get_viewer_url(),
        "properties": await utilities.get_table_columns(database, scheme, table, request.app),
        "geometrytype": await utilities.get_table_geometry_type(database, scheme, table, request.app),
        "type": "table",
        "minzoom": 0,
        "maxzoom": 22,
        "bounds": await utilities.get_table_bounds(database, scheme, table, request.app),
        "center": await utilities.get_table_center(database, scheme, table, request.app)
    }
