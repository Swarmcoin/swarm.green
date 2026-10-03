"""Integration: the real server on 127.0.0.1, exercised over HTTP the way the
Vercel function calls it (shared secret + X-Waitlist-Client-Ip)."""
import contextlib
import io
import json
import logging
import os
import re
import shutil
import socket
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request

from waitlist import addresses as A
from waitlist.config import Config
from waitlist.mail import Mailer, SUBJECT
from waitlist.web import App, make_server

S1 = "s1bbQ5zUoR3ttqKiNDVXGhy3NgoQWpWC7GL"
UA = ("swm1j77uutrvudh07mdxcynfzwxykzv3hcy2yjqn890feadhhpm35gakjp6vjcdwezg5yszkffe09zzg3vn9"
      "ulhjj8jlvhswqjlvk5c2wkxe")
ORIGIN = "http://localhost:4173"
SECRET = "s" * 20 + "ecret-for-the-tests-only-0123456789"


def ua():
    return A.encode_unified([(3, os.urandom(43))])


class Server:
    def __init__(self, **overrides):
        self.dir = tempfile.mkdtemp()
        env = {"WAITLIST_DATA_DIR": self.dir, "WAITLIST_ALLOWED_ORIGINS": ORIGIN,
               "WAITLIST_PUBLIC_BASE_URL": "http://localhost:4173", "WAITLIST_PROXY_SECRET": SECRET}
        env.update(overrides)
        self.sent = []
        self.cfg = Config.from_env(env)
        self.app = App(self.cfg, mailer=Mailer(self.cfg, sender=lambda cfg, msg: self.sent.append(msg)))
        self.app.store.migrate()
        self.httpd = make_server(self.app, host="127.0.0.1", port=0)
        self.port = self.httpd.server_address[1]
        self.base = "http://127.0.0.1:%d/waitlist/api/" % self.port
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        shutil.rmtree(self.dir, ignore_errors=True)

    def call(self, route, body=None, method=None, headers=None, raw=None, ip="93.184.216.34", secret=SECRET):
        h = {}
        if secret is not None:
            h["X-Waitlist-Proxy-Secret"] = secret
        if ip:
            h["X-Waitlist-Client-Ip"] = ip
        data = None
        if body is not None or raw is not None:
            data = raw if raw is not None else json.dumps(body).encode()
            h["Content-Type"] = "application/json"
            h["Origin"] = ORIGIN
        h.update(headers or {})
        req = urllib.request.Request(self.base + route, data=data, method=method, headers=h)
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, dict(r.headers), json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers), json.loads(e.read() or b"{}")


def join_body(email, address, invite=None, **extra):
    body = {"email": email, "address": address, "consent": True, "trap": ""}
    if invite:
        body["invite"] = invite
    body.update(extra)
    return body


def wait_for(cond, seconds=3):
    end = time.monotonic() + seconds
    while time.monotonic() < end and not cond():
        time.sleep(0.05)


class Endpoints(unittest.TestCase):
    def setUp(self):
        self.log = io.StringIO()
        self.handler = logging.StreamHandler(self.log)
        logging.getLogger("waitlist").addHandler(self.handler)
        logging.getLogger("waitlist").setLevel(logging.INFO)
        self.s = Server(WAITLIST_JOIN_PER_IP_PER_HOUR="3")

    def tearDown(self):
        self.s.close()
        logging.getLogger("waitlist").removeHandler(self.handler)

    def test_full_flow(self):
        s = self.s
        status, headers, body = s.call("healthz", secret=None, ip=None)
        self.assertEqual((status, body), (200, {"ok": True, "mail": "off"}))

        status, headers, stats = s.call("stats")
        self.assertEqual((status, stats["total"]), (200, 0))
        self.assertEqual(headers["Cache-Control"], "public, max-age=30")
        self.assertNotIn("Access-Control-Allow-Origin", headers)

        status, _, a = s.call("join", join_body("Alice@Example.com", UA))
        self.assertEqual(status, 201)
        self.assertEqual((a["position"], a["total"], a["mail"], a["inviteRule"], a["news"]),
                         (1, 1, "off", "all-entries", False))
        self.assertTrue(a["inviteUrl"].endswith("/waitlist?i=" + a["inviteCode"]))
        self.assertIn("key", a)

        status, _, b = s.call("join", join_body("bob@example.org", S1, invite=a["inviteCode"], news=True),
                              ip="8.8.8.8")
        self.assertEqual((status, b["invite"], b["position"], b["total"], b["news"]), (201, "counted", 2, 2, True))

        status, headers, board = s.call("leaderboard")
        self.assertEqual(status, 200)
        self.assertEqual(board["entries"][0]["label"], "swm1j77u…wkxe")
        self.assertEqual(board["entries"][0]["invites"], 1)
        text = json.dumps(board)
        for value in ("alice", "bob", UA, S1):
            self.assertNotIn(value, text)

        status, headers, me = s.call("me?key=" + a["key"])
        self.assertEqual((status, me["position"], me["invites"]), (200, 1, 1))
        self.assertEqual(headers["Cache-Control"], "no-store")
        status, _, me2 = s.call("me", {"key": b["key"]})
        self.assertEqual((me2["inviteCode"], me2["news"]), (b["inviteCode"], True))

        # Joining again with the same details: only the place, nothing to take over.
        status, _, again = s.call("join", join_body("alice@example.com", UA))
        self.assertEqual((status, again), (200, {"alreadyJoined": True, "position": 1}))

        # Same email with another address, or same address with another email:
        # one neutral sentence that does not say which one matched.
        status, _, err = s.call("join", join_body("alice@example.com", "s3fLmEHc1xqs8KAe7QS7oupkhuGDjidV4eq"),
                                ip="1.1.1.1")
        self.assertEqual((status, err), (409, {"error": "These details cannot be added to the list."}))
        status, _, err2 = s.call("join", join_body("carol@example.com", UA), ip="1.0.0.1")
        self.assertEqual((status, err2), (409, err))

        # Project news can be stopped without leaving the list.
        self.assertEqual(s.call("news", {"key": b["key"], "news": False})[0], 200)
        self.assertFalse(s.call("me", {"key": b["key"]})[2]["news"])

        # Bob leaves: his data goes, and his invite no longer counts for Alice.
        status, _, gone = s.call("delete", {"key": b["key"]})
        self.assertEqual((status, gone), (200, {"deleted": True}))
        self.assertEqual(s.call("me?key=" + b["key"])[0], 404)
        self.assertEqual(s.call("delete", {"key": b["key"]})[0], 404)
        self.assertEqual(s.call("stats")[2]["total"], 1)
        self.assertEqual(s.call("leaderboard")[2]["entries"][0]["invites"], 0)

        self.assertEqual(s.call("confirm?token=" + "x" * 22)[0], 409)
        self.assertEqual(s.sent, [])

        logs = self.log.getvalue()
        for value in ("alice", "bob", UA, S1, a["key"], b["key"], "93.184.216.34", "8.8.8.8", SECRET):
            self.assertNotIn(value.lower(), logs.lower())
        self.assertIn("join ok: new", logs)

    def test_secret_is_required_everywhere_but_healthz(self):
        s = self.s
        for route in ("stats", "leaderboard", "me?key=" + "k" * 22, "confirm?token=" + "t" * 22):
            self.assertEqual(s.call(route, secret=None)[0], 403, route)
            self.assertEqual(s.call(route, secret=SECRET[:-1] + "x")[0], 403, route)
        self.assertEqual(s.call("join", join_body("a@example.com", UA), secret=None)[0], 403)
        self.assertEqual(s.call("join", join_body("a@example.com", UA), secret="")[0], 403)
        self.assertEqual(s.call("stats")[2]["total"], 0)

    def test_forwarded_for_is_never_read(self):
        s = self.s
        # Four joins from one client address; a changing X-Forwarded-For does not help.
        codes = [s.call("join", join_body(f"x{i}@example.com", ua()), ip="9.9.9.9",
                        headers={"X-Forwarded-For": f"8.8.{i}.{i}"})[0] for i in range(4)]
        self.assertEqual(codes, [201, 201, 201, 429])

    def test_validation_errors_name_the_field(self):
        status, _, err = self.s.call("join", join_body("nope", UA), ip="1.0.0.2")
        self.assertEqual((status, err["field"]), (400, "email"))
        status, _, err = self.s.call("join", join_body("a@example.com", "swarm1" + "q" * 70), ip="1.0.0.3")
        self.assertEqual((status, err["field"]), (400, "address"))
        self.assertIn("testnet", err["error"])
        status, _, err = self.s.call("join", join_body("a@example.com", UA[:-1] + "q"), ip="1.0.0.4")
        self.assertEqual((status, err["field"]), (400, "address"))
        self.assertIn("checksum", err["error"])
        status, _, err = self.s.call("join", join_body("a@example.com", UA, consent=False), ip="1.0.0.5")
        self.assertEqual((status, err["field"], err["error"]),
                         (400, "consent", "Tick the first box to join the waiting list."))
        status, _, err = self.s.call("join", join_body("bad", "bad", consent=False), ip="1.0.0.6")
        self.assertEqual(set(err["fields"]), {"email", "address", "consent"})
        # Failed attempts count against the caller's own join limit (3 per hour here).
        for _ in range(3):
            self.s.call("join", join_body("bad", UA), ip="1.0.0.7")
        self.assertEqual(self.s.call("join", join_body("ok@example.com", UA), ip="1.0.0.7")[0], 429)

    def test_honeypot(self):
        for field in ("trap", "website"):
            status, _, _ = self.s.call("join", join_body("a@example.com", UA, **{field: "x"}), ip="2.2.2.2")
            self.assertEqual(status, 400)
        self.assertEqual(self.s.call("stats")[2]["total"], 0)

    def test_transport_rules(self):
        s = self.s
        big = json.dumps(join_body("a@example.com", UA, pad="x" * 5000)).encode()
        self.assertEqual(s.call("join", raw=big)[0], 413)
        self.assertEqual(s.call("join", raw=b"{}", headers={"Content-Type": "text/plain"})[0], 415)
        self.assertEqual(s.call("join", raw=b"[1,2]")[0], 400)
        self.assertEqual(s.call("join", raw=b"{not json")[0], 400)
        self.assertEqual(s.call("me", raw=b"[" * 2000 + b"]" * 2000)[0], 400)      # deep nesting
        self.assertEqual(s.call("me", raw=b'{"key": "\\ud800\\ud800\\ud800\\ud800\\ud800\\ud800\\ud800\\ud800"}')[0], 404)
        self.assertEqual(s.call("delete", raw=b'{"key": "\\udfff' + b"a" * 30 + b'"}')[0], 404)
        self.assertEqual(s.call("join", raw=json.dumps(join_body("a\udfff@example.com", UA),
                                                       ensure_ascii=True).encode())[0], 400)
        self.assertEqual(s.call("join", join_body("a@example.com", UA),
                                headers={"Origin": "https://evil.example"})[0], 403)
        self.assertEqual(s.call("nothing-here")[0], 404)
        self.assertEqual(s.call("join")[0], 405)              # GET on a POST route

    def test_unknown_routes_are_logged_as_other(self):
        self.s.call("secret-admin-panel")
        self.assertNotIn("secret-admin-panel", self.log.getvalue())
        self.assertIn("GET other 404", self.log.getvalue())


class GlobalLimit(unittest.TestCase):
    def test_only_created_entries_use_the_global_budget(self):
        s = Server(WAITLIST_JOIN_GLOBAL_PER_MINUTE="2")
        try:
            # Ten invalid attempts from ten addresses use none of it ...
            for i in range(10):
                self.assertEqual(s.call("join", join_body("bad", UA), ip=f"3.3.3.{i}")[0], 400)
            # ... nor does joining again with the same details.
            self.assertEqual(s.call("join", join_body("g0@example.com", UA), ip="1.1.1.1")[0], 201)
            self.assertEqual(s.call("join", join_body("g0@example.com", UA), ip="1.1.1.2")[0], 200)
            self.assertEqual(s.call("join", join_body("g1@example.com", S1), ip="8.8.8.8")[0], 201)
            status, _, err = s.call("join", join_body("g3@example.com", ua()), ip="9.9.9.9")
            self.assertEqual(status, 429)
            self.assertIn("minute", err["error"])
            # Validation still answers first when the global budget is spent.
            self.assertEqual(s.call("join", join_body("bad", UA), ip="9.9.9.8")[0], 400)
        finally:
            s.close()


class SlowClients(unittest.TestCase):
    def test_read_deadline_closes_a_dripping_connection(self):
        s = Server(WAITLIST_READ_DEADLINE_SECONDS="1")
        try:
            c = socket.create_connection(("127.0.0.1", s.port), timeout=5)
            c.sendall(b"POST /waitlist/api/join HTTP/1.1\r\nHost: x\r\nContent-Type: application/json\r\n"
                      b"Content-Length: 100\r\nX-Waitlist-Proxy-Secret: " + SECRET.encode() + b"\r\n\r\n{")
            started = time.monotonic()
            data = b""
            try:
                while True:
                    chunk = c.recv(4096)
                    if not chunk:
                        break
                    data += chunk
            except (ConnectionResetError, ConnectionAbortedError, socket.timeout):
                pass
            self.assertLess(time.monotonic() - started, 4)
            self.assertNotIn(b" 201 ", data)
            c.close()
        finally:
            s.close()

    def test_saturation_answers_503(self):
        s = Server(WAITLIST_MAX_WORKERS="1", WAITLIST_READ_DEADLINE_SECONDS="3")
        try:
            slow = socket.create_connection(("127.0.0.1", s.port), timeout=5)
            slow.sendall(b"GET /waitlist/api/stats HTTP/1.1\r\nHost: x\r\n")   # headers never finished
            time.sleep(0.3)
            status, _, body = s.call("healthz", secret=None)
            self.assertEqual(status, 503)
            self.assertIn("Busy", body["error"])
            slow.close()
            wait_for(lambda: s.call("healthz", secret=None)[0] == 200, seconds=6)
            self.assertEqual(s.call("healthz", secret=None)[0], 200)
        finally:
            s.close()


class Startup(unittest.TestCase):
    def test_production_needs_a_long_secret(self):
        with self.assertRaises(SystemExit):
            Config.from_env({})
        with self.assertRaises(SystemExit):
            Config.from_env({"WAITLIST_PROXY_SECRET": "short"})
        self.assertEqual(Config.from_env({"WAITLIST_PROXY_SECRET": "x" * 32}).mode, "production")
        self.assertEqual(Config.from_env({"WAITLIST_PROXY_SECRET": "dev", "WAITLIST_MODE": "development"}).mode,
                         "development")
        with self.assertRaises(SystemExit):
            Config.from_env({"WAITLIST_MODE": "development"})
        # Maintenance commands (backup, export, purge) run without it.
        Config.from_env({}, require_secret=False)


class MailFlow(unittest.TestCase):
    def test_confirmation_mail_and_confirm(self):
        s = Server(MAIL_MODE="smtp", SMTP_HOST="mail.invalid", MAIL_FROM="list@swarm.green")
        try:
            status, _, a = s.call("join", join_body("a@example.com", UA))
            self.assertEqual((status, a["mail"], a["inviteRule"]), (201, "on", "confirmed-only"))
            status, _, b = s.call("join", join_body("b@example.com", S1, invite=a["inviteCode"]), ip="8.8.8.8")
            self.assertEqual(b["invite"], "after-confirmation")
            wait_for(lambda: len(s.sent) == 2)
            self.assertEqual(len(s.sent), 2)
            msg = next(m for m in s.sent if m["To"] == "b@example.com")
            self.assertEqual(msg["Subject"], SUBJECT)
            text = msg.get_content()
            token = re.search(r"/waitlist#confirm=([A-Za-z0-9_-]+)", text).group(1)
            self.assertIn("/waitlist#remove=" + b["key"], text)
            self.assertIn("not a promise of coins", text)
            self.assertIn("31 October 2026, 15:42 UTC", text)
            self.assertEqual(s.call("leaderboard")[2]["entries"][0]["invites"], 0)
            self.assertEqual(s.call("confirm", {"token": token})[0], 200)
            self.assertEqual(s.call("leaderboard")[2]["entries"][0]["invites"], 1)
            self.assertEqual(s.call("confirm?token=" + token)[0], 404)
            self.assertTrue(s.call("me?key=" + b["key"])[2]["confirmed"])
        finally:
            s.close()

    def test_squatted_email_is_taken_back_by_confirming(self):
        s = Server(MAIL_MODE="smtp", SMTP_HOST="mail.invalid", MAIL_FROM="list@swarm.green")
        try:
            status, _, squat = s.call("join", join_body("victim@example.com", ua()), ip="6.6.6.6")
            self.assertEqual(status, 201)
            status, _, own = s.call("join", join_body("victim@example.com", S1), ip="7.7.7.7")
            self.assertEqual(status, 201)
            wait_for(lambda: len(s.sent) == 2)
            mail = next(m for m in s.sent if ("#remove=" + own["key"]) in m.get_content())
            token = re.search(r"#confirm=([A-Za-z0-9_-]+)", mail.get_content()).group(1)
            self.assertEqual(s.call("confirm", {"token": token})[0], 200)
            self.assertEqual(s.call("me", {"key": squat["key"]})[0], 404)
            self.assertEqual(s.call("stats")[2]["total"], 1)
        finally:
            s.close()

    def test_mail_failure_is_logged_without_details(self):
        cfg = Config.from_env({"MAIL_MODE": "smtp", "SMTP_HOST": "h", "MAIL_FROM": "f@swarm.green",
                               "SMTP_PASSWORD": "hunter2", "WAITLIST_DATA_DIR": tempfile.mkdtemp()},
                              require_secret=False)

        def boom(cfg, msg):
            raise ConnectionRefusedError("to a@example.com with hunter2")

        buf = io.StringIO()
        h = logging.StreamHandler(buf)
        logging.getLogger("waitlist").addHandler(h)
        try:
            Mailer(cfg, sender=boom).confirmation("a@example.com", "t" * 22, "k" * 22, wait=True)
        finally:
            logging.getLogger("waitlist").removeHandler(h)
        self.assertIn("ConnectionRefusedError", buf.getvalue())
        for value in ("a@example.com", "hunter2", "t" * 22, "k" * 22):
            self.assertNotIn(value, buf.getvalue())

    def test_mail_off_sends_nothing(self):
        cfg = Config.from_env({"WAITLIST_DATA_DIR": tempfile.mkdtemp()}, require_secret=False)
        sent = []
        self.assertIsNone(Mailer(cfg, sender=lambda c, m: sent.append(m)).confirmation("a@b.co", "t", "k", wait=True))
        self.assertEqual(sent, [])

    def test_smtp_needs_settings(self):
        with self.assertRaises(SystemExit):
            Config.from_env({"MAIL_MODE": "smtp"}, require_secret=False)
        with self.assertRaises(SystemExit):
            Config.from_env({"MAIL_MODE": "sendgrid"}, require_secret=False)


class Cli(unittest.TestCase):
    def test_purge_is_a_dry_run_unless_told(self):
        from waitlist.__main__ import main
        d = tempfile.mkdtemp()
        old = dict(os.environ)
        try:
            os.environ["WAITLIST_DATA_DIR"] = d
            os.environ.pop("WAITLIST_PROXY_SECRET", None)
            app = App(Config.from_env(require_secret=False))
            app.store.migrate()
            app.store.join("a@example.com", "a@example.com", UA, None, "x")
            app.store.join("b@example.com", "b@example.com", S1, None, "y", news=True)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(main(["purge", "--without-news-consent", "--before", "2999-01-01"]), 0)
            self.assertIn("dry run): 1 entries", out.getvalue())
            self.assertEqual(app.store.total(), 2)
            with contextlib.redirect_stdout(out):
                self.assertEqual(main(["purge", "--without-news-consent", "--before", "2999-01-01", "--yes"]), 0)
            self.assertIn("deleted 1 entries", out.getvalue())
            self.assertEqual(app.store.total(), 1)
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                main(["purge", "--before", "2999-01-01", "--yes"])   # the flag is required
        finally:
            os.environ.clear()
            os.environ.update(old)
            shutil.rmtree(d, ignore_errors=True)


class Salt(unittest.TestCase):
    def test_salt_is_generated_once_and_kept(self):
        d = tempfile.mkdtemp()
        try:
            cfg = Config.from_env({"WAITLIST_DATA_DIR": d}, require_secret=False)
            first = App(cfg).salt
            self.assertEqual(App(cfg).salt, first)
            self.assertEqual(len(first), 64)
            self.assertEqual(App(Config.from_env({"WAITLIST_DATA_DIR": d, "WAITLIST_IP_SALT": "env"},
                                                 require_secret=False)).salt, "env")
        finally:
            shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
