"""The HTTP API, on the standard library's threading HTTP server.

Every path lives under /waitlist/api/. JSON in, JSON out, no CORS headers.

Only the Vercel function api/waitlist/[...path].js may call it: every route
except healthz answers 403 unless X-Waitlist-Proxy-Secret equals
WAITLIST_PROXY_SECRET (constant-time compare). The client address comes only
from X-Waitlist-Client-Ip, and only on such a request.

Slow clients: each connection has a total deadline for its request line,
headers and body (WAITLIST_READ_DEADLINE_SECONDS, 10 s); at most
WAITLIST_MAX_WORKERS requests are handled at once, and a connection beyond that
gets 503 at once.

Logs carry the method, a known route name, the status and the time taken;
never a query string, a body, an address, an email, a key, a token or an IP.
"""
from __future__ import annotations

import hmac
import json
import logging
import os
import secrets
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from . import addresses, emails, limits
from .mail import Mailer
from .store import Conflict, Store, now_utc

log = logging.getLogger("waitlist.http")

PREFIX = "/waitlist/api/"
ROUTES = ("join", "stats", "leaderboard", "me", "delete", "confirm", "news", "healthz")
POST_ROUTES = ("join", "me", "delete", "confirm", "news")

MSG_CONSENT = "Tick the first box to join the waiting list."
MSG_CONFLICT = "These details cannot be added to the list."
MSG_GENERIC = "We could not add you just now. Please try again later."
MSG_RATE = "Too many attempts from your connection. Please wait a while and try again."
MSG_BUSY = "Many people are joining right now. Please try again in a minute."
MSG_NOT_FOUND = "This entry is not on the list (any more)."
HONEYPOTS = ("trap", "website")


def load_salt(cfg):
    if cfg.ip_salt:
        return cfg.ip_salt
    path = os.path.join(cfg.data_dir, "ip-salt")
    try:
        with open(path, encoding="ascii") as fh:
            salt = fh.read().strip()
        if salt:
            return salt
    except FileNotFoundError:
        pass
    os.makedirs(cfg.data_dir, exist_ok=True)
    salt = secrets.token_hex(32)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="ascii") as fh:
        fh.write(salt + "\n")
    log.info("generated a new IP salt in the data directory")
    return salt


class App:
    def __init__(self, cfg, store=None, mailer=None, clock=time.monotonic):
        self.cfg = cfg
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.store = store or Store(os.path.join(cfg.data_dir, "waitlist.sqlite3"),
                                    os.path.join(here, "migrations"), mail_on=cfg.mail_on)
        self.mailer = mailer or Mailer(cfg)
        self.limiter = limits.RateLimiter(clock=clock, max_keys=cfg.limiter_max_keys)
        self.salt = load_salt(cfg)
        self._secret = cfg.proxy_secret.encode("utf-8")
        self._cache = {}
        self._cache_lock = threading.Lock()

    def secret_ok(self, presented):
        if not self._secret or presented is None:
            return False
        try:
            given = presented.encode("utf-8")
        except UnicodeEncodeError:
            return False
        return hmac.compare_digest(given, self._secret)

    @property
    def invite_rule(self):
        return "confirmed-only" if self.cfg.mail_on else "all-entries"

    def invite_url(self, code):
        return f"{self.cfg.public_base_url}/waitlist?i={code}"

    # Small memo for the two public, cacheable reads; any write clears it.
    def cached(self, name, build, ttl=5.0):
        now = time.monotonic()
        with self._cache_lock:
            hit = self._cache.get(name)
            if hit and now - hit[0] < ttl:
                return hit[1]
        value = build()
        with self._cache_lock:
            self._cache[name] = (now, value)
        return value

    def invalidate(self):
        with self._cache_lock:
            self._cache.clear()

    # ------------------------------------------------------------ handlers
    def stats(self):
        return self.cached("stats", lambda: {"total": self.store.total(), "updatedUtc": now_utc()[:19] + "Z"})

    def leaderboard(self):
        def build():
            rows = self.store.leaderboard(self.cfg.leaderboard_size)
            return {"updatedUtc": now_utc()[:19] + "Z", "total": self.store.total(),
                    "inviteRule": self.invite_rule,
                    "entries": [{"rank": r["position"], "label": addresses.mask(r["address"]),
                                 "invites": r["invites"], "joinedUtc": r["joined_utc"][:10]} for r in rows]}
        return self.cached("leaderboard", build)

    def validate_join(self, body):
        """(fields, errors). Validation happens before any global limit."""
        fields = {}
        values = {}
        try:
            values["email"] = emails.validate(body.get("email"))
        except emails.EmailError as exc:
            fields["email"] = str(exc)
        try:
            values["address"], _kind = addresses.validate(body.get("address"))
        except addresses.AddressError as exc:
            fields["address"] = str(exc)
        if body.get("consent") is not True:
            fields["consent"] = MSG_CONSENT
        invite = body.get("invite")
        values["invite"] = invite if isinstance(invite, str) and invite else None
        values["news"] = body.get("news") is True
        return values, fields

    def join(self, values, ip_hash):
        try:
            res = self.store.join(values["email"], emails.canonical(values["email"]), values["address"],
                                  values["invite"], ip_hash, news=values["news"])
        except Conflict:
            log.info("join refused: conflict")
            return 409, {"error": MSG_CONFLICT}
        if not res["created"]:
            # Same email and address again: only the place, nothing that would
            # let a stranger who knows both take over the entry or its invites.
            log.info("join: already on the list")
            return 200, {"alreadyJoined": True, "position": res["position"]}
        self.invalidate()
        out = {"created": True, "position": res["position"], "total": res["total"],
               "invites": res["invites"], "inviteCode": res["inviteCode"],
               "inviteUrl": self.invite_url(res["inviteCode"]), "invite": res["invite"],
               "confirmed": False, "news": res["news"], "mail": "on" if self.cfg.mail_on else "off",
               "inviteRule": self.invite_rule, "key": res["key"]}
        if self.cfg.mail_on and res.get("confirmToken"):
            self.mailer.confirmation(values["email"], res["confirmToken"], res["key"])
        log.info("join ok: new")
        return 201, out

    def me(self, key):
        found = self.store.me(key)
        if found is None:
            return 404, {"error": MSG_NOT_FOUND}
        found.update(inviteUrl=self.invite_url(found["inviteCode"]), inviteRule=self.invite_rule,
                     mail="on" if self.cfg.mail_on else "off")
        return 200, found

    def delete(self, key):
        if not self.store.delete(key):
            return 404, {"error": MSG_NOT_FOUND}
        self.invalidate()
        log.info("entry deleted")
        return 200, {"deleted": True}

    def news(self, body):
        if body.get("news") is not False:
            return 400, {"error": "Only stopping project news is possible here."}
        if not self.store.stop_news(body.get("key")):
            return 404, {"error": MSG_NOT_FOUND}
        log.info("news consent withdrawn")
        return 200, {"news": False}

    def confirm(self, token):
        if not self.cfg.mail_on:
            return 409, {"error": "Email confirmation is not switched on yet."}
        removed = self.store.confirm(token)
        if removed is None:
            return 404, {"error": "This confirmation link is not valid (any more)."}
        self.invalidate()
        log.info("entry confirmed (%d unconfirmed holder(s) of the same email removed)", removed)
        return 200, {"confirmed": True}


class Handler(BaseHTTPRequestHandler):
    server_version = "waitlist"
    sys_version = ""
    timeout = 15
    app: App = None  # set by make_server

    # ------------------------------------------------------------ deadline
    def setup(self):
        super().setup()
        self._read_done = False
        self._timer = threading.Timer(self.app.cfg.read_deadline_seconds, self._expire)
        self._timer.daemon = True
        self._timer.start()

    def _expire(self):
        if not self._read_done:
            try:
                self.connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

    def _done_reading(self):
        self._read_done = True
        self._timer.cancel()

    def finish(self):
        self._timer.cancel()
        try:
            super().finish()
        except OSError:
            pass

    # ------------------------------------------------------------ logging
    def log_request(self, code="-", size="-"):
        pass  # one line per request is written in _handle instead

    def log_error(self, fmt, *args):
        log.info("protocol error")  # the default text can quote the raw request line

    def log_message(self, fmt, *args):
        pass

    # ------------------------------------------------------------ plumbing
    def _client(self):
        if not self._trusted:
            return None
        ip = limits.parse_client_ip(self.headers.get("X-Waitlist-Client-Ip"))
        return limits.ip_hash(ip, self.app.salt)

    def _send(self, status, payload, cache="no-store"):
        body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", cache)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)
        self._status = status

    def _body(self):
        """The JSON object in the body, or (status, error) to send."""
        if self.headers.get("Transfer-Encoding"):
            return None, (411, {"error": "Send a Content-Length."})
        ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        if ctype != "application/json":
            return None, (415, {"error": "Send JSON."})
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            return None, (411, {"error": "Send a Content-Length."})
        if length < 0 or length > self.app.cfg.max_body_bytes:
            self.close_connection = True
            return None, (413, {"error": "Too large."})
        raw = self.rfile.read(length) if length else b""
        if len(raw) != length:
            self.close_connection = True
            return None, (400, {"error": "Incomplete request."})
        self._done_reading()
        try:
            data = json.loads(raw.decode("utf-8")) if raw else {}
        except (UnicodeDecodeError, ValueError, RecursionError):
            return None, (400, {"error": "Send a JSON object."})
        if not isinstance(data, dict):
            return None, (400, {"error": "Send a JSON object."})
        return data, None

    def _origin_ok(self):
        origin = self.headers.get("Origin")
        return origin is None or origin in self.app.cfg.allowed_origins

    def _route(self):
        path = urlsplit(self.path).path
        if not path.startswith(PREFIX):
            return None
        return path[len(PREFIX):].strip("/")

    def _query(self, name):
        values = parse_qs(urlsplit(self.path).query).get(name)
        return values[0] if values else None

    def _handle(self):
        started = time.monotonic()
        self._status = 0
        route = self._route()
        if self.command in ("GET", "HEAD"):
            self._done_reading()
        try:
            self._dispatch(route)
        except (ConnectionError, TimeoutError, socket.timeout):
            self.close_connection = True
            log.info("connection closed before the answer (slow or gone)")
        except (RecursionError, UnicodeEncodeError, UnicodeDecodeError):
            if not self._status:
                self._send(400, {"error": "Bad request."})
        except Exception as exc:  # never echo internals
            log.error("handler error on %s: %s", route if route in ROUTES else "other", type(exc).__name__)
            if not self._status:
                try:
                    self._send(500, {"error": MSG_GENERIC})
                except Exception:
                    pass
        finally:
            log.info("%s %s %s %dms", self.command if self.command in ("GET", "HEAD", "POST") else "other",
                     route if route in ROUTES else "other", self._status or "-",
                     (time.monotonic() - started) * 1000)

    def _dispatch(self, route):
        app = self.app
        method = "GET" if self.command == "HEAD" else self.command
        if route is None or route not in ROUTES:
            return self._send(404, {"error": "Not found."})
        if route == "healthz":
            if method != "GET":
                return self._send(405, {"error": "Not found."})
            app.store.total()
            return self._send(200, {"ok": True, "mail": app.cfg.mail_mode})

        self._trusted = app.secret_ok(self.headers.get("X-Waitlist-Proxy-Secret"))
        if not self._trusted:
            return self._send(403, {"error": "Forbidden."})
        who = str(self._client() or "unknown")
        if not app.limiter.hit([("req:" + who, app.cfg.requests_per_ip_per_minute, 60)]):
            return self._send(429, {"error": MSG_RATE})

        if method == "GET":
            if route == "stats":
                return self._send(200, app.stats(), cache="public, max-age=30")
            if route == "leaderboard":
                return self._send(200, app.leaderboard(), cache="public, max-age=30")
            if route == "me":
                return self._send(*app.me(self._query("key")))
            if route == "confirm":
                return self._send(*app.confirm(self._query("token")))
            return self._send(405, {"error": "Not found."})
        if method != "POST" or route not in POST_ROUTES:
            return self._send(405, {"error": "Not found."})
        if not self._origin_ok():
            return self._send(403, {"error": "Forbidden."})
        body, err = self._body()
        if err:
            return self._send(*err)

        if route == "join":
            cfg = app.cfg
            mine = [("join-h:" + who, cfg.join_per_ip_per_hour, 3600),
                    ("join-d:" + who, cfg.join_per_ip_per_day, 86400)]
            # Every attempt counts against the caller's own limits ...
            if app.limiter.check(mine):
                log.info("join refused: rate limit")
                return self._send(429, {"error": MSG_RATE})
            if any(body.get(h) for h in HONEYPOTS):
                log.info("join refused: honeypot")
                return self._send(400, {"error": MSG_GENERIC})
            values, fields = app.validate_join(body)
            if fields:
                first = next(iter(fields))
                return self._send(400, {"error": fields[first], "field": first, "fields": fields})
            # ... the global limit only counts entries actually created.
            glob = [("join-global", cfg.join_global_per_minute, 60)]
            if app.limiter.peek(glob):
                log.info("join refused: global limit")
                return self._send(429, {"error": MSG_BUSY})
            status, out = app.join(values, None if who == "unknown" else who)
            if status == 201:
                app.limiter.record(glob)
            return self._send(status, out)
        if route == "me":
            return self._send(*app.me(body.get("key")))
        if route == "delete":
            return self._send(*app.delete(body.get("key")))
        if route == "news":
            return self._send(*app.news(body))
        if route == "confirm":
            return self._send(*app.confirm(body.get("token") or self._query("token")))

    def do_GET(self):
        self._handle()

    def do_HEAD(self):
        self._handle()

    def do_POST(self):
        self._handle()

    def do_PUT(self):
        self._handle()

    def do_DELETE(self):
        self._handle()


_BUSY = (b"HTTP/1.0 503 Service Unavailable\r\nContent-Type: application/json; charset=utf-8\r\n"
         b"Content-Length: 49\r\nCache-Control: no-store\r\nConnection: close\r\n\r\n"
         b'{"error":"Busy just now. Please try again soon."}')


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    request_queue_size = 64
    max_workers = 32

    def server_bind(self):
        self._slots = threading.BoundedSemaphore(self.max_workers)
        super().server_bind()

    def process_request(self, request, client_address):
        if not self._slots.acquire(blocking=False):
            try:
                request.settimeout(2)
                request.sendall(_BUSY)
            except OSError:
                pass
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self._slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._slots.release()


def make_server(app, host=None, port=None):
    handler = type("BoundHandler", (Handler,), {"app": app})
    server_cls = type("BoundServer", (Server,), {"max_workers": app.cfg.max_workers})
    return server_cls((host or app.cfg.host, app.cfg.port if port is None else port), handler)
