-- PostgreSQL schema per Kira
-- La memoria e knowledge sono gestite da Supermemory (cloud)
-- Qui solo tabelle custom: reminders e notes

CREATE TABLE IF NOT EXISTS reminders (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    due_at TIMESTAMPTZ NOT NULL,
    recurrence TEXT,              -- 'daily', 'weekly', 'monthly', NULL
    notified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS notes (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    tags TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indice per ricerca full-text sulle note
CREATE INDEX IF NOT EXISTS idx_notes_fts
    ON notes USING gin(to_tsvector('italian', title || ' ' || content));
