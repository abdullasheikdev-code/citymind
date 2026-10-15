PRAGMA foreign_keys = ON;

CREATE TABLE road_nodes (
    id              INTEGER PRIMARY KEY,
    osm_node_id     INTEGER,
    lat             REAL NOT NULL,
    lon             REAL NOT NULL,
    is_signal       INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE roads (
    id              INTEGER PRIMARY KEY,
    osm_way_id      INTEGER,
    name            TEXT NOT NULL,
    road_class      TEXT NOT NULL CHECK (road_class IN ('arterial', 'collector', 'local')),
    node_a          INTEGER NOT NULL REFERENCES road_nodes(id),
    node_b          INTEGER NOT NULL REFERENCES road_nodes(id),
    length_m        REAL NOT NULL,
    speed_kmph      INTEGER NOT NULL,
    capacity_vph    INTEGER NOT NULL,
    lanes           INTEGER NOT NULL DEFAULT 2,
    oneway          INTEGER NOT NULL DEFAULT 0,
    is_closed       INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE facilities (
    id              INTEGER PRIMARY KEY,
    facility_type   TEXT NOT NULL CHECK (facility_type IN
                        ('hospital', 'school', 'fire_station', 'police_station',
                         'bus_stop', 'parking')),
    name            TEXT NOT NULL,
    lat             REAL NOT NULL,
    lon             REAL NOT NULL,
    nearest_node_id INTEGER REFERENCES road_nodes(id),
    capacity        INTEGER
);

CREATE TABLE population_zones (
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL,
    centroid_lat    REAL NOT NULL,
    centroid_lon    REAL NOT NULL,
    nearest_node_id INTEGER REFERENCES road_nodes(id),
    population      INTEGER NOT NULL
);

CREATE TABLE scenarios (
    id              INTEGER PRIMARY KEY,
    scenario_type   TEXT NOT NULL,
    input_params    TEXT NOT NULL,
    result_json     TEXT NOT NULL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);