"""Integration: the real server on 127.0.0.1, exercised over HTTP."""
import io
import json
import logging
import os
import re
import shutil
import tempfile
import threading
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


class Server:
    def __init__(self, **overrides):
        self.dir = tempfile.mkdtemp()
        env = {"WAITLIST_DATA_DIR": self.dir, "WAITLIST_ALLOWED_ORIGINS": ORIGIN,
               "WAITLIST_PUBLIC_BASE_URL": "http://localhost:4173"}
        env.update(overrides)
        self.sent = []
        self.cfg = Config.from_env(env)
        self.app = App(self.cfg, mailer=Mailer(self.cfg, sender=lambda cfg, msg: self.sent.append(msg)))
        self.app.store.migrate()
        self.httpd = make_server(self.app, host="127.0.0.1", port=0)
        self.base = "http://127.0.0.1:%d/waitlist/api/" % self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        shutil.rmtree(self.dir, ignore_errors=True)

    def call(self, route, body=None, method=None, headers=None, raw=None, ip="93.184.216.34"):
        h = {"X-Forwarded-For": ip} if ip else {}
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
    body = {"email": email, "address": address, "consent": True, "website": ""}
    if invite:
        body["invite"] = invite
    body.update(extra)
    return body


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
        status, headers, body = s.call("healthz")
        self.assertEqual((status, body["ok"], body["mail"]), (200, True, "off"))
        self.assertEqual(body["forwardedHeaderUsed"], True)
        self.assertEqual(len(body["you"]), 8)

        status, headers, stats = s.call("stats")
        self.assertEqual((status, stats["total"]), (200, 0))
        self.assertEqual(headers["Cache-Control"], "public, max-age=30")
        self.assertNotIn("Access-Control-Allow-Origin", headers)

        status, _, a = s.call("join", join_body("Alice@Example.com", UA))
        self.assertEqual(status, 201)
        self.assertEqual((a["position"], a["total"], a["mail"], a["inviteRule"]), (1, 1, "off", "all-entries"))
        self.assertTrue(a["inviteUrl"].endswith("/waitlist?i=" + a["inviteCode"]))
        self.assertIn("key", a)

        # The second person joins through the first person's invite, from elsewhere.
        status, _, b = s.call("join", join_body("bob@example.org", S1, invite=a["inviteCode"]), ip="8.8.8.8")
        self.assertEqual((status, b["invite"], b["position"], b["total"]), (201, "counted", 2, 2))

        status, headers, board = s.call("leaderboard")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Cache-Control"], "public, max-age=30")
        self.assertEqual(board["entries"][0], {"rank": 1, "label": "swm1j77u…wkxe", "invites": 1,
                                               "joinedUtc": board["entries"][0]["joinedUtc"]})
        text = json.dumps(board)
        self.assertNotIn("alice", text.lower())
        self.assertNotIn(UA, text)
        self.assertNotIn("bob", text)

        # Own entry, by GET (as specified) and by POST (what the page uses).
        status, headers, me = s.call("me?key=" + a["key"])
        self.assertEqual((status, me["position"], me["invites"]), (200, 1, 1))
        self.assertEqual(headers["Cache-Control"], "no-store")
        status, _, me2 = s.call("me", {"key": a["key"]})
        self.assertEqual(me2["inviteCode"], a["inviteCode"])

        # Joining again with the same details returns the entry, without the key.
        status, _, again = s.call("join", join_body("alice@example.com", UA))
        self.assertEqual((status, again["created"], again["inviteCode"]), (200, False, a["inviteCode"]))
        self.assertNotIn("key", again)

        # Same email, other address: a plain error that reveals nothing.
        status, _, err = s.call("join", join_body("alice@example.com", "s3fLmEHc1xqs8KAe7QS7oupkhuGDjidV4eq"),
                                ip="1.1.1.1")
        self.assertEqual(status, 409)
        self.assertNotIn("alice", err["error"].lower())

        # Bob leaves: his data goes, Alice keeps her one invite.
        status, _, gone = s.call("delete", {"key": b["key"]})
        self.assertEqual((status, gone), (200, {"deleted": True}))
        self.assertEqual(s.call("me?key=" + b["key"])[0], 404)
        self.assertEqual(s.call("delete", {"key": b["key"]})[0], 404)
        self.assertEqual(s.call("stats")[2]["total"], 1)
        self.assertEqual(s.call("leaderboard")[2]["entries"][0]["invites"], 1)

        # Confirmation is off.
        self.assertEqual(s.call("confirm?token=" + "x" * 22)[0], 409)
        self.assertEqual(s.sent, [])

        logs = self.log.getvalue()
        for secret in ("alice", "bob", UA, S1, a["key"], b["key"], "93.184.216.34", "8.8.8.8"):
            self.assertNotIn(secret.lower(), logs.lower())
        self.assertIn("join ok: new", logs)

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
        self.assertEqual((status, err["field"]), (400, "consent"))
        status, _, err = self.s.call("join", join_body("bad", "bad", consent=False), ip="1.0.0.6")
        self.assertEqual(set(err["fields"]), {"email", "address", "consent"})
        # Failed attempts count against the join limit too (3 per hour in this test).
        for _ in range(3):
            self.s.call("join", join_body("bad", UA), ip="1.0.0.7")
        self.assertEqual(self.s.call("join", join_body("ok@example.com", UA), ip="1.0.0.7")[0], 429)

    def test_honeypot(self):
        status, _, err = self.s.call("join", join_body("a@example.com", UA, website="http://spam"))
        self.assertEqual(status, 400)
        self.assertEqual(self.s.call("stats")[2]["total"], 0)

    def test_transport_rules(self):
        s = self.s
        big = json.dumps(join_body("a@example.com", UA, pad="x" * 5000)).encode()
        self.assertEqual(s.call("join", raw=big)[0], 413)
        self.assertEqual(s.call("join", raw=b"{}", headers={"Content-Type": "text/plain"})[0], 415)
        self.assertEqual(s.call("join", raw=b"[1,2]")[0], 400)
        self.assertEqual(s.call("join", raw=b"{not json")[0], 400)
        self.assertEqual(s.call("join", join_body("a@example.com", UA),
                                headers={"Origin": "https://evil.example"})[0], 403)
        self.assertEqual(s.call("nothing-here")[0], 404)
        self.assertEqual(s.call("join")[0], 405)              # GET on a POST route

    def test_join_rate_limit_per_ip(self):
        s = self.s
        for i in range(3):
            self.assertEqual(s.call("join", join_body(f"p{i}@example.com", A.encode_unified(
                [(3, os.urandom(43))])), ip="9.9.9.9")[0], 201)
        status, _, err = s.call("join", join_body("p9@example.com", S1), ip="9.9.9.9")
        self.assertEqual(status, 429)
        # another connection is not affected
        self.assertEqual(s.call("join", join_body("q@example.com", S1), ip="1.0.0.1")[0], 201)

    def test_untrusted_peer_cannot_choose_its_address(self):
        s = Server(WAITLIST_TRUSTED_PROXIES="203.0.113.0/24", WAITLIST_JOIN_PER_IP_PER_HOUR="1")
        try:
            # Peer 127.0.0.1 is not trusted now, so the header is ignored and
            # both requests count against the same address.
            self.assertEqual(s.call("join", join_body("a@example.com", UA), ip="8.8.8.8")[0], 201)
            self.assertEqual(s.call("join", join_body("b@example.com", S1), ip="1.1.1.1")[0], 429)
        finally:
            s.close()

    def test_global_join_limit(self):
        s = Server(WAITLIST_JOIN_GLOBAL_PER_MINUTE="2")
        try:
            for i, ip in enumerate(("1.1.1.1", "8.8.8.8")):
                self.assertEqual(s.call("join", join_body(f"g{i}@example.com", A.encode_unified(
                    [(3, os.urandom(43))])), ip=ip)[0], 201)
            status, _, err = s.call("join", join_body("g3@example.com", S1), ip="9.9.9.9")
            self.assertEqual(status, 429)
            self.assertIn("minute", err["error"])
        finally:
            s.close()


class MailFlow(unittest.TestCase):
    def test_confirmation_mail_and_confirm(self):
        s = Server(MAIL_MODE="smtp", SMTP_HOST="mail.invalid", MAIL_FROM="list@swarm.green")
        try:
            status, _, a = s.call("join", join_body("a@example.com", UA))
            self.assertEqual((status, a["mail"], a["inviteRule"]), (201, "on", "confirmed-only"))
            status, _, b = s.call("join", join_body("b@example.com", S1, invite=a["inviteCode"]), ip="8.8.8.8")
            self.assertEqual(b["invite"], "after-confirmation")
            for _ in range(50):
                if len(s.sent) == 2:
                    break
                threading.Event().wait(0.05)
            self.assertEqual(len(s.sent), 2)
            msg = s.sent[1]
            self.assertEqual(msg["Subject"], SUBJECT)
            self.assertEqual(msg["To"], "b@example.com")
            text = msg.get_content()
            token = re.search(r"/waitlist#confirm=([A-Za-z0-9_-]+)", text).group(1)
            self.assertIn("/waitlist#remove=" + b["key"], text)
            self.assertIn("not a promise of coins", text)
            self.assertEqual(s.call("leaderboard")[2]["entries"][0]["invites"], 0)
            self.assertEqual(s.call("confirm", {"token": token})[0], 200)
            self.assertEqual(s.call("leaderboard")[2]["entries"][0]["invites"], 1)
            self.assertEqual(s.call("confirm?token=" + token)[0], 404)
            self.assertTrue(s.call("me?key=" + b["key"])[2]["confirmed"])
        finally:
            s.close()

    def test_mail_failure_is_logged_without_details(self):
        cfg = Config.from_env({"MAIL_MODE": "smtp", "SMTP_HOST": "h", "MAIL_FROM": "f@swarm.green",
                               "SMTP_PASSWORD": "hunter2", "WAITLIST_DATA_DIR": tempfile.mkdtemp()})

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
        for secret in ("a@example.com", "hunter2", "t" * 22, "k" * 22):
            self.assertNotIn(secret, buf.getvalue())

    def test_mail_off_sends_nothing(self):
        cfg = Config.from_env({"WAITLIST_DATA_DIR": tempfile.mkdtemp()})
        sent = []
        self.assertIsNone(Mailer(cfg, sender=lambda c, m: sent.append(m)).confirmation("a@b.co", "t", "k", wait=True))
        self.assertEqual(sent, [])

    def test_smtp_needs_settings(self):
        with self.assertRaises(SystemExit):
            Config.from_env({"MAIL_MODE": "smtp"})
        with self.assertRaises(SystemExit):
            Config.from_env({"MAIL_MODE": "sendgrid"})


class Salt(unittest.TestCase):
    def test_salt_is_generated_once_and_kept(self):
        d = tempfile.mkdtemp()
        try:
            cfg = Config.from_env({"WAITLIST_DATA_DIR": d})
            first = App(cfg).salt
            self.assertEqual(App(cfg).salt, first)
            self.assertEqual(len(first), 64)
            self.assertEqual(App(Config.from_env({"WAITLIST_DATA_DIR": d, "WAITLIST_IP_SALT": "env"})).salt, "env")
        finally:
            shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
