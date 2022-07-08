# FastVector

FastVector is a [PostGIS](https://github.com/postgis/postgis) [vector tiles](https://github.com/mapbox/vector-tile-spec) built for serving large geometric tables. FastVector is written in [Python](https://www.python.org/) using the [FastAPI](https://fastapi.tiangolo.com/) web framework. 

FastVector is built with inspriration from [TiMVT](https://github.com/developmentseed/timvt).

It defers from TiMVT in the fact that it has multi server/database support, cql_filtering, and a fields parameter.

---

**Source Code**: <a href="https://github.com/mkeller3/FastVector" target="_blank">https://github.com/mkeller3/FastVector</a>

---

## Requirements

FastVector requires PostGIS >= 2.4.0.

## Configuration

In order for the api to work you will need to edit the `config.py` file with your database connections.

Example
```python
DATABASES = {
    "data": {
        "host": "localhost", # Hostname of the server
        "database": "data", # Name of the database
        "username": "postgres", # Name of the user, ideally only SELECT rights
        "password": "postgres", # Password of the user
        "port": 5432, # Port number for PostgreSQL
        "cache_age_in_seconds": 6000, # Number of seconds for tile to be cache in clients browser. You can set to zero if you do not want any caching.
        "max_features_per_tile": 100000 # Maximum features per tile. This helps with performance for tables with a large number of rows.
    }
}
```

## Usage

### Running Locally

To run the app locally `uvicorn main:app --reload`

### Production
Build Dockerfile into a docker image to deploy to the cloud.

## API

| Method | URL                                                                              | Description                                             |
| ------ | -------------------------------------------------------------------------------- | ------------------------------------------------------- |
| `GET`  | `/api/v1/table/tables.json`                                                            | [Tables](#tables)               |
| `GET`  | `/api/v1/table/{database}/{scheme}/{table}.json`                                 | [Table JSON](#table-json)         |
| `GET`  | `/api/v1/tiles/{database}/{scheme}/{table}/{z}/{x}/{y}.pbf`                      | [Tiles](#tiles)    |
| `GET`  | `/api/v1/tiles/{database}/{scheme}/{table}.json`                                  | [Table TileJSON](#table-tile-json) |
| `DELETE` | `/api/v1/tiles/cache`                                                               | [Delete Cache](#cache-delete)  |
| `GET`  | `/api/v1/tiles/cache_size`                                                             | [Cache Size](#cache-size) |
| `GET`  | `/viewer/{database}/{scheme}/{table}`                                            | [Viewer](#viewer)               |
| `GET`  | `/api/v1/health_check`                                                           | Server health check: returns `200 OK`            |

## Using with Mapbox GL JS

[Mapbox GL JS](https://github.com/mapbox/mapbox-gl-js) is a JavaScript library for interactive, customizable vector maps on the web. It takes map styles that conform to the
[Mapbox Style Specification](https://www.mapbox.com/mapbox-gl-js/style-spec), applies them to vector tiles that
conform to the [Mapbox Vector Tile Specification](https://github.com/mapbox/vector-tile-spec), and renders them using
WebGL.

You can add a layer to the map and specify TileJSON endpoint as a vector source URL. You should also specify a `source-layer` property. For [Table JSON](#table-json) it is `{schema_name}.{table_name}` by default.

```js
map.addSource('points', {
  type: 'vector',
  url: `http://localhost:8000/api/v1/tiles/data/public/state_centroids/{z}/{x}/{y}.pbf`
});

map.addLayer({
  'id': 'state_centroids',
  'type': 'circle',
  'source': 'state_centroids',
  'source-layer': 'public.state_centroids',
  'paint': {
    'circle-color': 'red'
  }
});
```


## Using with MapLibre
[MapLibre](https://maplibre.org/projects/maplibre-gl-js/) is an Open-source JavaScript library for publishing maps on your websites. 

```js
map.addSource('state_centroids', {
  type: 'vector',
  url: `http://localhost:8000/api/v1/tiles/data/public/state_centroids/{z}/{x}/{y}.pbf`
});

map.addLayer({
  'id': 'points',
  'type': 'circle',
  'source': 'state_centroids',
  'source-layer': 'public.state_centroids',
  'paint': {
    'circle-color': 'red'
  }
});
```

## Using with Leaflet

[Leaflet](https://github.com/Leaflet/Leaflet) is the leading open-source JavaScript library for mobile-friendly interactive maps.

You can add vector tiles using [Leaflet.VectorGrid](https://github.com/Leaflet/Leaflet.VectorGrid) plugin. You must initialize a [VectorGrid.Protobuf](https://leaflet.github.io/Leaflet.VectorGrid/vectorgrid-api-docs.html#vectorgrid-protobuf) with a URL template, just like in L.TileLayers. The difference is that you should define the styling for all the features.

```js
L.vectorGrid
  .protobuf('http://localhost:8000/api/v1/tiles/data/public/state_centroids/{z}/{x}/{y}.pbf', {
    vectorTileLayerStyles: {
      'public.state_centroids': {
        color: 'red',
        fill: true
      }
    }
  })
  .addTo(map);
```

## Tables
Tables endpoint provides a listing of all the tables available to query as vector tiles.


Tables endpoint is available at `/api/v1/table/tables.json`

```shell
curl http://localhost:8000/api/v1/table/tables.json
```

Example Response
```json
[
  {
    "name": "states",
    "schema": "public",
    "type": "table",
    "id": "public.states",
    "database": "data",
    "detailurl": "http://127.0.0.1:8000/api/v1/table/data/public/states.json",
    "viewerurl": "http://127.0.0.1:8000/viewer/data/public/states"
  },
  {},...
```

## Table JSON

Table endpoint is available at `/api/v1/table/{database}/{scheme}/{table}.json`

For example, `states` table in `public` schema in `data` database will be available at `/api/v1/table/data/public/states.json`

```shell
curl http://localhost:8000/api/v1/table/data/public/states.json
```

Example Response
```json
{
  "id": "public.states",
  "schema": "public",
  "tileurl": "http://127.0.0.1:8000/api/v1/tiles/data/public/states/{z}/{x}/{y}.pbf",
  "viewerurl": "http://127.0.0.1:8000/viewer/data/public/states",
  "properties": [
    {
      "name": "gid",
      "type": "integer",
      "description": null
    },
    {
      "name": "geom",
      "type": "geometry",
      "description": null
    },
    {
      "name": "state_name",
      "type": "character varying",
      "description": null
    },
    {
      "name": "state_fips",
      "type": "character varying",
      "description": null
    },
    {
      "name": "state_abbr",
      "type": "character varying",
      "description": null
    },
    {
      "name": "population",
      "type": "integer",
      "description": null
    }
  ],
  "geometrytype": "ST_MultiPolygon",
  "type": "table",
  "minzoom": 0,
  "maxzoom": 22,
  "bounds": [
    -178.2175984,
    18.9217863,
    -66.9692709999999,
    71.406235408712
  ],
  "center": [
    -112.96125695842262,
    45.69082939790446
  ]
}
```

## Tiles

Tiles endpoint is available at `/api/v1/tiles/{database}/{scheme}/{table}/{z}/{x}/{y}.pbf`

For example, `states` table in `public` schema in `data` database will be available at `/api/v1/table/data/public/states/{z}/{x}/{y}.pbf`

### Fields

If you have a table with a large amount of fields you can limit the amount of fields returned using the fields parameter.

#### Note

If you use the fields parameter the tile will not be cached on the server.

For example, if we only want the `state_fips` field.

`/api/v1/table/data/public/states/{z}/{x}/{y}.pbf?fields=state_fips`

### CQL Filtering

CQL filtering is enabled via [pygeofilter](https://pygeofilter.readthedocs.io/en/latest/index.html). This allows you to dynamically filter your tiles database size for larger tiles.

For example, filter the states layer to only show states with a population greater than 1,000,000.

`/api/v1/table/data/public/states/{z}/{x}/{y}.pbf?cql_filter=population>1000000`

[Geoserver](https://docs.geoserver.org/stable/en/user/tutorials/cql/cql_tutorial.html) has examples of using cql filters.

#### Spatial Filters

| Filters | 
| --- |
| Intersects |
| Equals |
| Disjoint |
| Touches |
| Within |
| Overlaps |
| Crosses |
| Contains |

#### Note

If you use the cql_filter parameter the tile will not be cached on the server.

## Table Tile JSON

Table [TileJSON](https://github.com/mapbox/tilejson-spec) endpoint is available at `/api/v1/tiles/{database}/{scheme}/{table}.json`

For example, `states` table in `public` schema in `data` database will be available at `/api/v1/tiles/data/public/states.json`

```shell
curl http://localhost:8000/api/v1/tiles/data/public/states.json
```

Example Response
```json
{
  "tilejson": "2.2.0",
  "name": "public.states",
  "version": "1.0.0",
  "scheme": "xyz",
  "tiles": [
    "http://127.0.0.1:8000/api/v1/tiles/data/public/states/{z}/{x}/{y}.pbf"
  ],
  "viewerurl": "http://127.0.0.1:8000/viewer/data/public/states",
  "minzoom": 0,
  "maxzoom": 22
}
```

## Cache Delete
The cache delete endpoint allows you to delete any vector tile cache on the server.

This is a DELETE HTTP method endpoint.

In your request you have to pass the following.

```json
{
  "database": "data",
  "scheme": "public",
  "table": "states"
}
```

## Cache Size
Cache Size endpoint allows you to determine the size of a vector tile cache for each table.

```shell
curl http://localhost:8000/api/v1/api/v1/tiles/cache_size
```

Example Response
```json
[
  {
    "table": "data_public_counties",
    "size_in_gigabytes": 0.004711238
  },
  {
    "table": "data_public_states",
    "size_in_gigabytes": 0.000034666
  }
]
```

## Viewer
The viewer allows to preview a tile dataset in a web map viewer. 

For example, you can view the states table at `/viewer/data/public/states`. It will automatically zoom to the extent of the table.



![Viewer Image](/images/viewer_demo.png "Viewer Image")
