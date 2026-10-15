CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE road_nodes (
    id              BIGSERIAL PRIMARY KEY,
    osm_node_id     BIGINT,
    lat             DOUBLE PRECISION NOT NULL,
    lon             DOUBLE PRECISION NOT NULL,
    geom            GEOMETRY(Point, 4326) NOT NULL,
    is_signal       BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE INDEX idx_road_nodes_geom ON road_nodes USING GIST (geom);

CREATE TABLE roads (
    id              BIGSERIAL PRIMARY KEY,
    osm_way_id      BIGINT,
    name            TEXT NOT NULL,
    road_class      TEXT NOT NULL CHECK (road_class IN ('arterial', 'collector', 'local')),
    node_a          BIGINT NOT NULL REFERENCES road_nodes(id),
    node_b          BIGINT NOT NULL REFERENCES road_nodes(id),
    length_m        DOUBLE PRECISION NOT NULL,
    speed_kmph      INTEGER NOT NULL,
    capacity_vph    INTEGER NOT NULL,
    lanes           INTEGER NOT NULL DEFAULT 2,
    oneway          BOOLEAN NOT NULL DEFAULT FALSE,
    geom            GEOMETRY(LineString, 4326) NOT NULL,
    is_closed       BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE INDEX idx_roads_geom ON roads USING GIST (geom);
CREATE INDEX idx_roads_node_a ON roads(node_a);
CREATE INDEX idx_roads_node_b ON roads(node_b);

CREATE TABLE facilities (
    id              BIGSERIAL PRIMARY KEY,
    facility_type   TEXT NOT NULL CHECK (facility_type IN
                        ('hospital', 'school', 'fire_station', 'police_station',
                         'bus_stop', 'parking')),
    name            TEXT NOT NULL,
    lat             DOUBLE PRECISION NOT NULL,
    lon             DOUBLE PRECISION NOT NULL,
    geom            GEOMETRY(Point, 4326) NOT NULL,
    nearest_node_id BIGINT REFERENCES road_nodes(id),
    capacity        INTEGER,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_facilities_geom ON facilities USING GIST (geom);
CREATE INDEX idx_facilities_type ON facilities(facility_type);

CREATE TABLE population_zones (
    id              BIGSERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    centroid_lat    DOUBLE PRECISION NOT NULL,
    centroid_lon    DOUBLE PRECISION NOT NULL,
    geom            GEOMETRY(Point, 4326) NOT NULL,
    nearest_node_id BIGINT REFERENCES road_nodes(id),
    population      INTEGER NOT NULL
);
CREATE INDEX idx_zones_geom ON population_zones USING GIST (geom);

CREATE TABLE scenarios (
    id              BIGSERIAL PRIMARY KEY,
    scenario_type   TEXT NOT NULL,
    input_params    JSONB NOT NULL,
    result_json     JSONB NOT NULL,
    created_by      BIGINT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);