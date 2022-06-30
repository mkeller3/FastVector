import os
import json
from fastapi import FastAPI
from pygeofilter.backends.sql import to_sql_where
from pygeofilter.parsers.ecql import parse

import config

async def get_tile(database: str, scheme: str, table: str, z: int, x: int, y: int, fields: str, cql_filter: str, db_settings: object, app: FastAPI) -> bytes:

    cachefile = f'{os.getcwd()}/cache/{database}_{scheme}_{table}/{z}/{x}/{y}'

    if os.path.exists(cachefile):
        return '', True

    pool = app.state.databases[f'{database}_pool']

    async with pool.acquire() as con:

        
        sql_field_query = f"""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = '{table}'
        AND column_name != 'geom';
        """
        
        field_mapping = {}

        db_fields = await con.fetch(sql_field_query)

        for field in db_fields:
            field_mapping[field['column_name']] = field['column_name']

        if fields is None:
            field_list = ""

            for field in db_fields:
                field_list += f", {field['column_name']}"
        else:
            field_list = f",{fields}"
        
        sql_vector_query = f"""
        SELECT ST_AsMVT(tile, '{scheme}.{table}', 4096)
        FROM (
            WITH
            bounds AS (
                SELECT ST_TileEnvelope({z}, {x}, {y}) as geom
            )
            SELECT
                st_asmvtgeom(
                    ST_Transform(t.geom, 3857)
                    ,bounds.geom
                ) AS mvtgeom {field_list}
            FROM {scheme}.{table} as t, bounds
            WHERE ST_Intersects(
                ST_Transform(t.geom, 4326),
                ST_Transform(bounds.geom, 4326)
            ) 	

        """
        if cql_filter:
            ast = parse(cql_filter)
            where_statement = to_sql_where(ast, field_mapping)
            sql_vector_query += f" AND {where_statement}"

        sql_vector_query += f"LIMIT {db_settings['max_features_per_tile']}) as tile"
        
        tile = await con.fetchval(sql_vector_query)

        if fields is None and cql_filter is None and db_settings['cache_age_in_seconds'] > 0:

            cachefile_dir = f'{os.getcwd()}/cache/{database}_{scheme}_{table}/{z}/{x}'

            if not os.path.exists(cachefile_dir):
                try:
                    os.makedirs(cachefile_dir)
                except OSError:
                    pass

            with open(cachefile, "wb") as f:
                f.write(tile)
                f.close()

        return tile, False

async def get_tables_metadata(app: FastAPI) -> list:
    tables_metadata = []
    for database in config.DATABASES:

        pool = app.state.databases[f'{database}_pool']

        async with pool.acquire() as con:
            tables_query = """
            SELECT schemaname, tablename
            FROM pg_catalog.pg_tables
            WHERE schemaname not in ('pg_catalog','information_schema', 'topology')
            AND tablename != 'spatial_ref_sys'; 
            """
            tables = await con.fetch(tables_query)
            for table in tables:
                tables_metadata.append(
                    {
                        "name" : table['tablename'],
                        "schema" : table['schemaname'],
                        "type" : "table",
                        "id" : f"{table['schemaname']}.{table['tablename']}",
                        "database" : config.DATABASES[database]['database']
                    }
                )
    
    return tables_metadata

async def get_table_columns(database: str, scheme: str, table: str, app: FastAPI) -> list:
    pool = app.state.databases[f'{database}_pool']

    async with pool.acquire() as con:
        column_query = f"""
        SELECT
            jsonb_agg(
                jsonb_build_object(
                    'name', attname,
                    'type', format_type(atttypid, null),
                    'description', col_description(attrelid, attnum)
                )
            )
        FROM pg_attribute
        WHERE attnum>0
        AND attrelid=format('%I.%I', '{scheme}', '{table}')::regclass
        """
        columns = await con.fetchval(column_query)
        return json.loads(columns)

async def get_table_geometry_type(database: str, scheme: str, table: str, app: FastAPI) -> list:
    pool = app.state.databases[f'{database}_pool']

    async with pool.acquire() as con:
        geometry_query = f"""
        SELECT ST_GeometryType(geom) as geom_type
        FROM {scheme}.{table}
        """
        geometry_type = await con.fetchval(geometry_query)
        return geometry_type

async def get_table_center(database: str, scheme: str, table: str, app: FastAPI) -> list:
    pool = app.state.databases[f'{database}_pool']

    async with pool.acquire() as con:
        query = f"""
        SELECT ST_X(ST_Centroid(ST_Union(geom))) as x,
        ST_Y(ST_Centroid(ST_Union(geom))) as y
        FROM {scheme}.{table}
        """
        center = await con.fetch(query)
        return [center[0][0],center[0][1]]

async def get_table_bounds(database: str, scheme: str, table: str, app: FastAPI) -> list:
    pool = app.state.databases[f'{database}_pool']

    async with pool.acquire() as con:
        query = f"""
        SELECT ARRAY[
            ST_XMin(ST_Union(geom)),
            ST_YMin(ST_Union(geom)),
            ST_XMax(ST_Union(geom)),
            ST_YMax(ST_Union(geom))
        ]
        FROM {scheme}.{table}
        """
        extent = await con.fetchval(query)
        
        return extent