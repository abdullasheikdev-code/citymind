CREATE TABLE users (
    id              INTEGER PRIMARY KEY,
    email           TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    password_salt   TEXT NOT NULL,
    role            TEXT NOT NULL CHECK (role IN ('admin', 'planner', 'viewer')),
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE audit_log (
    id              INTEGER PRIMARY KEY,
    user_id         INTEGER REFERENCES users(id),
    action          TEXT NOT NULL,
    detail_json     TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE kb_documents (
    id              INTEGER PRIMARY KEY,
    filename        TEXT NOT NULL,
    title           TEXT,
    uploaded_by     INTEGER REFERENCES users(id),
    uploaded_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE kb_chunks (
    id              INTEGER PRIMARY KEY,
    document_id     INTEGER NOT NULL REFERENCES kb_documents(id),
    chunk_index     INTEGER NOT NULL,
    content         TEXT NOT NULL,
    page_number     INTEGER
);

ALTER TABLE scenarios ADD COLUMN created_by INTEGER REFERENCES users(id);