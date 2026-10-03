"""SQLite storage: migrations, the join/confirm/delete rules, ranking, purge,
backup and export. Standard library only.

Ranking: position = order by (invites desc, joined asc, id asc).

Invites, one level only: an entry counts for the entry whose invite code it
used (its direct inviter) and for nobody else; invites of invites are never
counted. It counts exactly once, and never for the inviter itself: an entry
with the inviter's email mailbox, address or IP hash does not count. While
mail confirmation is on, only confirmed entries count. An invite that is
removed from the list no longer counts: the count is always the number of
live, eligible invitees.

Email ownership: with mail off, the first entry for a mailbox owns it. With
mail on, an unconfirmed entry does not own its email: another entry may be
created with the same email (and its own address), and the first of them to
confirm keeps the email; the other unconfirmed holders are then removed,
together with the invites they had collected.
"""
from __future__ import annotations

import csv
import datetime as dt
import glob
import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import threading

CODE_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"  # no 0/O, 1/I/L
CODE_LEN = 10
_SECRET_RE = re.compile(r"^[A-Za-z0-9_-]{16,64}$")


class Conflict(Exception):
    """Email or address already on the list with different details."""


def now_utc():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def sha256_hex(text):
    return hashlib.sha256(text.encode("ascii")).hexdigest()


def well_formed_secret(value):
    return isinstance(value, str) and bool(_SECRET_RE.match(value))


def new_key():
    return secrets.token_urlsafe(16)          # 128 random bits


def new_code():
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LEN))


def normalise_code(code):
    if not isinstance(code, str):
        return None
    code = code.strip().upper()
    if not 8 <= len(code) <= 10 or any(c not in CODE_ALPHABET for c in code):
        return None
    return code


_RANKED = """
WITH counted AS (
    SELECT invited_by AS id, COUNT(*) AS n
      FROM entries
     WHERE invited_by IS NOT NULL AND invite_eligible = 1
       AND (:mail_on = 0 OR confirmed_utc IS NOT NULL)
     GROUP BY invited_by
),
ranked AS (
    SELECT e.id, e.address, e.joined_utc, e.invite_code, e.confirmed_utc,
           COALESCE(c.n, 0) AS invites
      FROM entries e LEFT JOIN counted c ON c.id = e.id
)
SELECT id, address, joined_utc, invite_code, confirmed_utc, invites,
       ROW_NUMBER() OVER (ORDER BY invites DESC, joined_utc ASC, id ASC) AS position
  FROM ranked
"""


class Store:
    def __init__(self, path, migrations_dir, mail_on=False):
        self.path = path
        self.migrations_dir = migrations_dir
        self.mail_on = bool(mail_on)
        self._write = threading.Lock()

    # ------------------------------------------------------------ plumbing
    def connect(self):
        conn = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 10000")
        conn.execute("PRAGMA secure_delete = ON")
        return conn

    def migrate(self):
        """Applies every migrations/NNNN_*.sql not applied yet, in order."""
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        conn = self.connect()
        applied = []
        try:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations "
                         "(version TEXT PRIMARY KEY, applied_utc TEXT NOT NULL)")
            done = {r[0] for r in conn.execute("SELECT version FROM schema_migrations")}
            for file in sorted(glob.glob(os.path.join(self.migrations_dir, "*.sql"))):
                version = os.path.basename(file).split("_", 1)[0]
                if version in done:
                    continue
                with open(file, encoding="utf-8") as fh:
                    sql = fh.read()
                with self._write:
                    conn.execute("BEGIN IMMEDIATE")
                    try:
                        for statement in _statements(sql):
                            conn.execute(statement)
                        conn.execute("INSERT INTO schema_migrations VALUES (?, ?)", (version, now_utc()))
                        conn.execute("COMMIT")
                    except Exception:
                        conn.execute("ROLLBACK")
                        raise
                applied.append(version)
        finally:
            conn.close()
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass
        return applied

    def _params(self):
        return {"mail_on": 1 if self.mail_on else 0}

    def _tx(self, conn, fn):
        with self._write:
            conn.execute("BEGIN IMMEDIATE")
            try:
                result = fn()
                conn.execute("COMMIT")
                return result
            except BaseException:
                conn.execute("ROLLBACK")
                raise

    # ------------------------------------------------------------ reads
    def total(self, conn=None):
        own = conn is None
        conn = conn or self.connect()
        try:
            return conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
        finally:
            if own:
                conn.close()

    def ranking(self, conn=None, limit=None):
        own = conn is None
        conn = conn or self.connect()
        try:
            sql = _RANKED + (" ORDER BY position LIMIT :limit" if limit else " ORDER BY position")
            params = self._params()
            if limit:
                params["limit"] = int(limit)
            return [dict(r) for r in conn.execute(sql, params)]
        finally:
            if own:
                conn.close()

    def _ranked_one(self, conn, entry_id):
        row = conn.execute("SELECT * FROM (" + _RANKED + ") WHERE id = :id",
                           dict(self._params(), id=entry_id)).fetchone()
        return dict(row) if row else None

    def leaderboard(self, size=50):
        return self.ranking(limit=size)

    def _by_key(self, conn, key):
        if not well_formed_secret(key):
            return None
        want = sha256_hex(key)
        row = conn.execute("SELECT * FROM entries WHERE key_hash = ?", (want,)).fetchone()
        if row is None or not hmac.compare_digest(row["key_hash"], want):
            return None
        return row

    def me(self, key):
        conn = self.connect()
        try:
            row = self._by_key(conn, key)
            if row is None:
                return None
            ranked = self._ranked_one(conn, row["id"])
            return {"position": ranked["position"], "invites": ranked["invites"],
                    "inviteCode": row["invite_code"], "joinedUtc": row["joined_utc"][:10],
                    "confirmed": row["confirmed_utc"] is not None,
                    "news": row["news_consent_utc"] is not None,
                    "total": self.total(conn)}
        finally:
            conn.close()

    # ------------------------------------------------------------ writes
    def join(self, email, email_canon, address, invite_code, ip_hash, news=False):
        """Adds a person, or reports their existing entry when the same email
        mailbox and address come again. Raises Conflict when either is already
        used with a different partner (see the module notes on ownership)."""
        code = normalise_code(invite_code) if invite_code else None
        conn = self.connect()
        try:
            result = self._tx(conn, lambda: self._join(conn, email, email_canon, address, code,
                                                       bool(invite_code), ip_hash, bool(news)))
            ranked = self._ranked_one(conn, result["id"])
            result.update(position=ranked["position"], invites=ranked["invites"], total=self.total(conn))
            return result
        finally:
            conn.close()

    def _join(self, conn, email, email_canon, address, code, code_given, ip_hash, news):
        by_addr = conn.execute("SELECT * FROM entries WHERE address = ?", (address,)).fetchone()
        if by_addr is not None:
            if by_addr["email_canon"] == email_canon:
                return {"id": by_addr["id"], "created": False}
            raise Conflict()
        holders = conn.execute("SELECT confirmed_utc FROM entries WHERE email_canon = ?", (email_canon,)).fetchall()
        if holders:
            # Mail off: the first entry owns the mailbox. Mail on: only a
            # confirmed entry owns it; unconfirmed ones wait for confirmation.
            if not self.mail_on or any(h["confirmed_utc"] is not None for h in holders):
                raise Conflict()

        inviter = None
        if code:
            inviter = conn.execute("SELECT * FROM entries WHERE invite_code = ?", (code,)).fetchone()
        if inviter is None:
            invite_state = "unknown" if code_given else "none"
            eligible = 0
        else:
            same = (inviter["email_canon"] == email_canon or inviter["address"] == address
                    or (ip_hash is not None and inviter["ip_hash"] == ip_hash))
            eligible = 0 if same else 1
            invite_state = "not-counted" if same else ("after-confirmation" if self.mail_on else "counted")

        key = new_key()
        token = new_key() if self.mail_on else None
        stamp = now_utc()
        for _ in range(20):
            mine = new_code()
            if conn.execute("SELECT 1 FROM entries WHERE invite_code = ?", (mine,)).fetchone() is None:
                break
        else:
            raise RuntimeError("could not find a free invite code")
        cur = conn.execute(
            "INSERT INTO entries (email, email_canon, address, key_hash, invite_code, invited_by, "
            "invite_eligible, ip_hash, joined_utc, consent_utc, news_consent_utc, confirm_token_hash) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (email, email_canon, address, sha256_hex(key), mine,
             inviter["id"] if inviter is not None else None, eligible, ip_hash, stamp, stamp,
             stamp if news else None, sha256_hex(token) if token else None))
        return {"id": cur.lastrowid, "created": True, "inviteCode": mine, "key": key,
                "confirmToken": token, "invite": invite_state, "confirmed": False, "news": news}

    def confirm(self, token):
        """Marks the entry confirmed. Other UNCONFIRMED entries with the same
        mailbox are removed (with their invites). Returns the number of entries
        removed that way, or None for an unknown token."""
        if not well_formed_secret(token):
            return None
        want = sha256_hex(token)
        conn = self.connect()

        def work():
            row = conn.execute("SELECT id, email_canon, confirm_token_hash FROM entries "
                               "WHERE confirm_token_hash = ?", (want,)).fetchone()
            if row is None or not hmac.compare_digest(row["confirm_token_hash"], want):
                return None
            conn.execute("UPDATE entries SET confirmed_utc = ?, confirm_token_hash = NULL WHERE id = ?",
                         (now_utc(), row["id"]))
            cur = conn.execute("DELETE FROM entries WHERE email_canon = ? AND id != ? AND confirmed_utc IS NULL",
                               (row["email_canon"], row["id"]))
            return cur.rowcount

        try:
            return self._tx(conn, work)
        finally:
            conn.close()

    def delete(self, key):
        """Removes the entry and everything personal in it. An invite it was
        counted as stops counting."""
        conn = self.connect()

        def work():
            row = self._by_key(conn, key)
            if row is None:
                return False
            conn.execute("DELETE FROM entries WHERE id = ?", (row["id"],))
            return True

        try:
            return self._tx(conn, work)
        finally:
            conn.close()

    def stop_news(self, key):
        """Withdraws the optional consent to project news; the entry stays."""
        conn = self.connect()

        def work():
            row = self._by_key(conn, key)
            if row is None:
                return False
            conn.execute("UPDATE entries SET news_consent_utc = NULL WHERE id = ?", (row["id"],))
            return True

        try:
            return self._tx(conn, work)
        finally:
            conn.close()

    def purge_without_news_consent(self, before_utc, dry_run=True):
        """Entries without news consent that joined before ``before_utc``
        (ISO date or timestamp): counted, and deleted unless dry_run."""
        conn = self.connect()

        def work():
            n = conn.execute("SELECT COUNT(*) FROM entries WHERE news_consent_utc IS NULL AND joined_utc < ?",
                             (before_utc,)).fetchone()[0]
            if not dry_run and n:
                conn.execute("DELETE FROM entries WHERE news_consent_utc IS NULL AND joined_utc < ?",
                             (before_utc,))
            return n

        try:
            n = self._tx(conn, work)
            if not dry_run and n:
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            return n
        finally:
            conn.close()

    # ------------------------------------------------------------ operations
    def backup(self, dest_dir, keep=14):
        """A consistent copy through SQLite's online backup API, then rotation."""
        os.makedirs(dest_dir, mode=0o700, exist_ok=True)
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        target = os.path.join(dest_dir, f"waitlist-{stamp}.sqlite3")
        src = self.connect()
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        os.close(fd)
        dst = sqlite3.connect(target)
        try:
            src.backup(dst)
        finally:
            dst.close()
            src.close()
        os.chmod(target, 0o600)
        return target, _rotate(dest_dir, "waitlist-*.sqlite3", keep)

    def export(self, dest_dir, keep=5):
        """CSV for the operator: email, address, joined, confirmed,
        news_consent, invites, position. Mode 0600, newest ``keep`` kept.
        Cells a spreadsheet would run as a formula get a leading quote."""
        os.makedirs(dest_dir, mode=0o700, exist_ok=True)
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        target = os.path.join(dest_dir, f"waitlist-{stamp}.csv")
        conn = self.connect()
        try:
            ranked = {r["id"]: r for r in self.ranking(conn)}
            rows = conn.execute("SELECT id, email, address, joined_utc, confirmed_utc, news_consent_utc "
                                "FROM entries").fetchall()
        finally:
            conn.close()
        rows = sorted(rows, key=lambda r: ranked[r["id"]]["position"])
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
            out = csv.writer(fh)
            out.writerow(["email", "address", "joined", "confirmed", "news_consent", "invites", "position"])
            for r in rows:
                rk = ranked[r["id"]]
                out.writerow([_cell(r["email"]), _cell(r["address"]), r["joined_utc"],
                              r["confirmed_utc"] or "", r["news_consent_utc"] or "",
                              rk["invites"], rk["position"]])
        os.chmod(target, 0o600)
        return target, len(rows), _rotate(dest_dir, "waitlist-*.csv", keep)


def _rotate(folder, pattern, keep):
    files = sorted(glob.glob(os.path.join(folder, pattern)))
    removed = files[:-keep] if keep > 0 else []
    for old in removed:
        os.remove(old)
    return removed


def _cell(value):
    value = str(value)
    return "'" + value if value[:1] in ("=", "+", "-", "@", "\t", "\r") else value


def _statements(sql):
    """Splits a plain migration file on semicolons that end a line. Migration
    files hold DDL only (no triggers), so this is enough."""
    lines = [ln for ln in sql.splitlines() if not ln.strip().startswith("--")]
    out, buf = [], []
    for ln in lines:
        buf.append(ln)
        if ln.rstrip().endswith(";"):
            stmt = "\n".join(buf).strip()
            if stmt.strip(";").strip():
                out.append(stmt)
            buf = []
    tail = "\n".join(buf).strip()
    if tail:
        out.append(tail)
    return out
