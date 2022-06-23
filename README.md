# FastVector

FastVector is a [PostGIS](https://github.com/postgis/postgis) [vector tiles](https://github.com/mapbox/vector-tile-spec) built for serving large geometric tables. FastVector is written in [Python](https://www.python.org/) using the [FastAPI](https://fastapi.tiangolo.com/) web framework. 

FastVector is built with inspriration from [TiMVT](https://github.com/developmentseed/timvt).

---

**Source Code**: <a href="https://github.com/mkeller3/FastVector" target="_blank">https://github.com/mkeller3/FastVector</a>

---

## Requirements

FastVector requires PostGIS >= 2.4.0.

## Usage

### Running Locally

To run the app locally `uvicorn main:app --reload`

### Production
Build Dockerfile into a docker image to deploy to the cloud.

## API

| Method | URL                                                                              | Description                                             |
| ------ | -------------------------------------------------------------------------------- | ------------------------------------------------------- |
| `GET`  | `/api/v1/tables.json`                                                            | [Tables](#tables)               |
| `GET`  | `/api/v1/table/{database}/{scheme}/{table}.json`                                 | [Table JSON](#table-json)         |
| `GET`  | `/api/v1/tiles/{database}/{scheme}/{table}/{z}/{x}/{y}.pbf`                      | [Tiles](#tiles)               |
| `GET`  | `/api/v1/tile/{database}/{scheme}/{table}.json`                                  | [Table TileJSON](#tiles-json)               |
| `GET`  | `/api/v1/cache_size`                                                             | [Cache Size](#cache)           |
| `DELETE`  | `/api/v1/cache`                                                               | [Delete Cache](#delete-cache)           |
| `GET`  | `/viewer/{database}/{scheme}/{table}`                                            | [Viewer](#viewer)               |
| `GET`  | `/api/v1/health_check`                                                           | Server health check: returns `200 OK`            |

## Using with Mapbox GL JS

[Mapbox GL JS](https://github.com/mapbox/mapbox-gl-js) is a JavaScript library for interactive, customizable vector maps on the web. It takes map styles that conform to the
[Mapbox Style Specification](https://www.mapbox.com/mapbox-gl-js/style-spec), applies them to vector tiles that
conform to the [Mapbox Vector Tile Specification](https://github.com/mapbox/vector-tile-spec), and renders them using
WebGL.

You can add a layer to the map and specify martin TileJSON endpoint as a vector source URL. You should also specify a `source-layer` property. For [Table Sources](#table-sources) it is `{schema_name}.{table_name}` by default.

```js
map.addSource('points', {
  type: 'vector',
  url: `http://localhost:8000/api/v1/tiles/gisdata/public/state_centroids/{z}/{x}/{y}.pbf`
});

map.addLayer({
  id: 'state_centroids',
  type: 'circle',
  source: 'state_centroids',
  'source-layer': 'public.state_centroids',
  paint: {
    'circle-color': 'red'
  }
});
```


## Using with MapLibre
[MapLibre](https://maplibre.org/projects/maplibre-gl-js/) is an Open-source JavaScript library for publishing maps on your websites. 

```js
map.addSource('state_centroids', {
  type: 'vector',
  url: `http://localhost:8000/api/v1/tiles/gisdata/public/state_centroids/{z}/{x}/{y}.pbf`
});

map.addLayer({
  id: 'points',
  type: 'circle',
  source: 'state_centroids',
  'source-layer': 'public.state_centroids',
  paint: {
    'circle-color': 'red'
  }
});
```

## Using with Leaflet

[Leaflet](https://github.com/Leaflet/Leaflet) is the leading open-source JavaScript library for mobile-friendly interactive maps.

You can add vector tiles using [Leaflet.VectorGrid](https://github.com/Leaflet/Leaflet.VectorGrid) plugin. You must initialize a [VectorGrid.Protobuf](https://leaflet.github.io/Leaflet.VectorGrid/vectorgrid-api-docs.html#vectorgrid-protobuf) with a URL template, just like in L.TileLayers. The difference is that you should define the styling for all the features.

```js
L.vectorGrid
  .protobuf('http://localhost:8000/api/v1/tiles/gisdata/public/state_centroids/{z}/{x}/{y}.pbf', {
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

## Table JSON

## Tiles

## Tiles JSON

## Cache

## Cache Delete

## Viewer