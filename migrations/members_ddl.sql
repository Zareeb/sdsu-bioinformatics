CREATE TABLE IF NOT EXISTS members (
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    major TEXT,
    status TEXT,
    email TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    position TEXT NOT NULL DEFAULT '',
    public INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_members_name
    ON members (last_name, first_name);