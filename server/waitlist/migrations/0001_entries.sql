-- The waiting list. One row per person. Personal data in this table: email,
-- address and ip_hash (a salted hash, never the address itself). Deleting a row
-- deletes all of it; invite_departed keeps an inviter's count as a bare number.
CREATE TABLE entries (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    email              TEXT    NOT NULL,
    email_canon        TEXT    NOT NULL UNIQUE,
    address            TEXT    NOT NULL UNIQUE,
    key_hash           TEXT    NOT NULL UNIQUE,     -- sha256 of the private key, hex
    invite_code        TEXT    NOT NULL UNIQUE,
    invited_by         INTEGER REFERENCES entries(id) ON DELETE SET NULL,
    invite_eligible    INTEGER NOT NULL DEFAULT 0,  -- 1: may count for invited_by
    invite_departed    INTEGER NOT NULL DEFAULT 0,  -- counted invitees who removed themselves
    ip_hash            TEXT,
    joined_utc         TEXT    NOT NULL,            -- ISO 8601, microseconds, Z
    consent_utc        TEXT    NOT NULL,
    confirmed_utc      TEXT,
    confirm_token_hash TEXT    UNIQUE               -- sha256 of the token, hex
);
CREATE INDEX entries_invited_by ON entries(invited_by);
CREATE INDEX entries_joined ON entries(joined_utc, id);
