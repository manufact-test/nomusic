-- Non-destructive loudness setting scoped to a replacement, shared assets unchanged.
ALTER TABLE track_replacements ADD COLUMN gain_db DECIMAL(4,1) NOT NULL DEFAULT 0.0;
