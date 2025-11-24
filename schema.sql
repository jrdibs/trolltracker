DROP TABLE IF EXISTS entries;

CREATE TABLE entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    troll_count INTEGER NOT NULL,
    entry_date DATE NOT NULL
);