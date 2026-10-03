-- The waiting list. One row per entry. Personal data in this table: email,
-- address and ip_hash (a salted hash, never the address itself). Deleting a row
-- deletes all of it (PRAGMA secure_delete is on, so the freed pages are zeroed).
--
-- email_canon is deliberately not UNIQUE: while mail confirmation is on, an
-- unconfirmed entry does not own its email, and several unconfirmed entries
-- may share one until one of them confirms (store.py enforces the rules).
CREATE TABLE entries (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    email              TEXT    NOT NULL,
    email_canon        TEXT    NOT NULL,
    address            TEXT    NOT NULL UNIQUE,
    key_hash           TEXT    NOT NULL UNIQUE,     -- sha256 of the private key, hex
    invite_code        TEXT    NOT NULL UNIQUE,
    invited_by         INTEGER REFERENCES entries(id) ON DELETE SET NULL,
    invite_eligible    INTEGER NOT NULL DEFAULT 0,  -- 1: may count for invited_by
    ip_hash            TEXT,
    joined_utc         TEXT    NOT NULL,            -- ISO 8601, microseconds, Z
    consent_utc        TEXT    NOT NULL,            -- consent to the waiting list
    news_consent_utc   TEXT,                        -- optional consent to project news; NULL = none
    confirmed_utc      TEXT,
    confirm_token_hash TEXT    UNIQUE               -- sha256 of the token, hex
);
CREATE INDEX entries_email_canon ON entries(email_canon);
CREATE INDEX entries_invited_by ON entries(invited_by);
CREATE INDEX entries_joined ON entries(joined_utc, id);
