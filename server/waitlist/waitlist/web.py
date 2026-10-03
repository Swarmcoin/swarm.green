"""The HTTP API, on the standard library's threading HTTP server.

Every path lives under /waitlist/api/ (the server's Caddy passes that prefix
through unchanged). JSON in, JSON out. No CORS headers: the browser reaches
this through a same-origin rewrite on swarm.green.

Logs carry the method, the route name, the status and the time taken; never a
query string, a body, an address, an email, a key, a token or an IP address.
"""
from __future__ import annotations

import json
import logging
import os
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from . import addresses, emails, limits
from .mail import Mailer
from .store import Conflict, Store, now_utc

log = logging.getLogger("waitlist.http")

PREFIX = "/waitlist/api/"

MSG_CONSENT = "Tick the box to agree that we store your email and SWARM address for the waiting list."
MSG_CONFLICT = ("We could not add these details. If you joined before, use the same email "
                "and SWARM address as then.")
MSG_GENERIC = "We could not add you just now. Please try again later."
MSG_RATE = "Too many attempts from your connection. Please wait a while and try again."
MSG_BUSY = "Many people are joining right now. Please try again in a minute."
MSG_NOT_FOUND = "This entry is not on the list (any more)."


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
        self.limiter = limits.RateLimiter(clock=clock)
        self.trusted = limits.parse_networks(cfg.trusted_proxies)
        self.salt = load_salt(cfg)
        self._cache = {}
        self._cache_lock = threading.Lock()

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

    def join(self, body, ip_hash):
        fields = {}
        if body.get("website"):
            # The honeypot is a field people never see. Say nothing useful.
            log.info("join refused: honeypot")
            return 400, {"error": MSG_GENERIC}
        try:
            email = emails.validate(body.get("email"))
        except emails.EmailError as exc:
            fields["email"] = str(exc)
        try:
            address, _kind = addresses.validate(body.get("address"))
        except addresses.AddressError as exc:
            fields["address"] = str(exc)
        if body.get("consent") is not True:
            fields["consent"] = MSG_CONSENT
        invite = body.get("invite")
        if invite is not None and not isinstance(invite, str):
            invite = None
        if fields:
            first = next(iter(fields))
            return 400, {"error": fields[first], "field": first, "fields": fields}
        try:
            res = self.store.join(email, emails.canonical(email), address, invite or None, ip_hash)
        except Conflict:
            log.info("join refused: conflict")
            return 409, {"error": MSG_CONFLICT}
        self.invalidate()
        out = {"created": res["created"], "position": res["position"], "total": res["total"],
               "invites": res["invites"], "inviteCode": res["inviteCode"],
               "inviteUrl": self.invite_url(res["inviteCode"]), "invite": res["invite"],
               "confirmed": res["confirmed"], "mail": "on" if self.cfg.mail_on else "off",
               "inviteRule": self.invite_rule}
        if res["created"]:
            out["key"] = res["key"]
            if self.cfg.mail_on and res.get("confirmToken"):
                self.mailer.confirmation(email, res["confirmToken"], res["key"])
        log.info("join ok: %s", "new" if res["created"] else "existing")
        return (201 if res["created"] else 200), out

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

    def confirm(self, token):
        if not self.cfg.mail_on:
            return 409, {"error": "Email confirmation is not switched on yet."}
        if not self.store.confirm(token):
            return 404, {"error": "This confirmation link is not valid (any more)."}
        self.invalidate()
        log.info("entry confirmed")
        return 200, {"confirmed": True}


class Handler(BaseHTTPRequestHandler):
    server_version = "waitlist"
    sys_version = ""
    timeout = 15
    app: App = None  # set by make_server

    # ------------------------------------------------------------ logging
    def log_request(self, code="-", size="-"):
        pass  # one line per request is written in _finish instead

    def log_error(self, fmt, *args):
        log.info("protocol error")  # the default text can quote the raw request line

    def log_message(self, fmt, *args):
        pass

    # ------------------------------------------------------------ plumbing
    def _client(self):
        ip = limits.client_ip(self.client_address[0], self.headers.get("X-Forwarded-For"),
                              self.app.trusted, self.app.cfg.client_ip_mode)
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
        try:
            data = json.loads(raw.decode("utf-8")) if raw else {}
        except (UnicodeDecodeError, ValueError):
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
        try:
            self._dispatch(route)
        except Exception as exc:  # never echo internals
            log.error("handler error on %s: %s", route, type(exc).__name__)
            if not self._status:
                try:
                    self._send(500, {"error": MSG_GENERIC})
                except Exception:
                    pass
        finally:
            log.info("%s %s %s %dms", self.command, route if route is not None else "-",
                     self._status or "-", (time.monotonic() - started) * 1000)

    def _dispatch(self, route):
        app = self.app
        method = "GET" if self.command == "HEAD" else self.command
        if route is None:
            return self._send(404, {"error": "Not found."})
        if route == "healthz" and method == "GET":
            app.store.total()
            info = limits.forwarded_info(self.client_address[0], self.headers.get("X-Forwarded-For"),
                                         app.trusted)
            you = self._client()
            return self._send(200, dict(ok=True, mail=app.cfg.mail_mode, you=(you or "")[:8], **info))

        who = self._client()
        if not app.limiter.hit([("req:" + str(who), app.cfg.requests_per_ip_per_minute, 60)]):
            return self._send(429, {"error": MSG_RATE})

        if route == "stats" and method == "GET":
            return self._send(200, app.stats(), cache="public, max-age=30")
        if route == "leaderboard" and method == "GET":
            return self._send(200, app.leaderboard(), cache="public, max-age=30")
        if route == "me" and method == "GET":
            return self._send(*app.me(self._query("key")))
        if route == "confirm" and method == "GET":
            return self._send(*app.confirm(self._query("token")))

        if method != "POST" or route not in ("join", "me", "delete", "confirm"):
            return self._send(404 if route not in ("join", "me", "delete", "confirm", "stats",
                                                   "leaderboard") else 405, {"error": "Not found."})
        if not self._origin_ok():
            return self._send(403, {"error": "Forbidden."})
        body, err = self._body()
        if err:
            return self._send(*err)
        if route == "join":
            cfg = app.cfg
            refused = app.limiter.check([("join-global", cfg.join_global_per_minute, 60),
                                         ("join-h:" + str(who), cfg.join_per_ip_per_hour, 3600),
                                         ("join-d:" + str(who), cfg.join_per_ip_per_day, 86400)])
            if refused:
                log.info("join refused: rate limit")
                return self._send(429, {"error": MSG_BUSY if refused == "join-global" else MSG_RATE})
            return self._send(*app.join(body, who))
        if route == "me":
            return self._send(*app.me(body.get("key")))
        if route == "delete":
            return self._send(*app.delete(body.get("key")))
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


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    request_queue_size = 64


def make_server(app, host=None, port=None):
    handler = type("BoundHandler", (Handler,), {"app": app})
    return Server((host or app.cfg.host, app.cfg.port if port is None else port), handler)
