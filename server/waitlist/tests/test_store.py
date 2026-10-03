import csv
import os
import shutil
import sqlite3
import tempfile
import time
import unittest

from waitlist import addresses as A
from waitlist.emails import canonical
from waitlist.store import CODE_ALPHABET, Conflict, Store

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIGRATIONS = os.path.join(HERE, "migrations")


def ua():
    return A.encode_unified([(0x03, os.urandom(43))])


class Base(unittest.TestCase):
    mail_on = False

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.store = Store(os.path.join(self.dir, "w.sqlite3"), MIGRATIONS, mail_on=self.mail_on)
        self.store.migrate()

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def join(self, email, invite=None, ip="ip-" + "0" * 8, address=None, news=False):
        return self.store.join(email, canonical(email), address or ua(), invite, ip, news=news)

    def invites_of(self, entry):
        return {r["id"]: r for r in self.store.ranking()}[entry["id"]]["invites"]

    def position_of(self, entry):
        return {r["id"]: r for r in self.store.ranking()}[entry["id"]]["position"]


class Migrations(Base):
    def test_idempotent(self):
        self.assertEqual(self.store.migrate(), [])
        conn = sqlite3.connect(self.store.path)
        self.assertEqual(conn.execute("PRAGMA journal_mode").fetchone()[0], "wal")
        self.assertEqual(conn.execute("SELECT version FROM schema_migrations").fetchall(), [("0001",)])
        conn.close()


class Joining(Base):
    def test_new_entry(self):
        r = self.join("a@example.com")
        self.assertTrue(r["created"])
        self.assertEqual((r["position"], r["total"], r["invites"], r["invite"]), (1, 1, 0, "none"))
        self.assertEqual(len(r["inviteCode"]), 10)
        self.assertTrue(set(r["inviteCode"]) <= set(CODE_ALPHABET))
        self.assertGreaterEqual(len(r["key"]), 22)          # 128 bits, base64url
        self.assertNotEqual(r["key"], r["inviteCode"])

    def test_key_is_stored_only_as_a_hash(self):
        r = self.join("a@example.com")
        conn = sqlite3.connect(self.store.path)
        dump = "\n".join(conn.iterdump())
        conn.close()
        self.assertNotIn(r["key"], dump)

    def test_idempotent_same_email_and_address(self):
        addr = ua()
        first = self.join("a@example.com", address=addr)
        again = self.join("A@Example.com".lower(), address=addr)
        self.assertFalse(again["created"])
        self.assertNotIn("key", again)
        self.assertNotIn("inviteCode", again)
        self.assertEqual((again["position"], again["total"]), (1, 1))

    def test_plus_tag_is_the_same_person(self):
        addr = ua()
        self.join("ab@gmail.com", address=addr)
        again = self.join("a.b+list@googlemail.com", address=addr)
        self.assertFalse(again["created"])
        with self.assertRaises(Conflict):
            self.join("a.b+other@gmail.com")              # same mailbox, other address

    def test_conflicts(self):
        addr = ua()
        self.join("a@example.com", address=addr)
        with self.assertRaises(Conflict):
            self.join("a@example.com")                     # same email, other address
        with self.assertRaises(Conflict):
            self.join("b@example.com", address=addr)       # same address, other email
        self.assertEqual(self.store.total(), 1)

    def test_unknown_invite_code(self):
        r = self.join("a@example.com", invite="ZZZZZZZZZZ")
        self.assertEqual(r["invite"], "unknown")
        r = self.join("b@example.com", invite="not a code!")
        self.assertEqual(r["invite"], "unknown")

    def test_invite_code_is_case_insensitive(self):
        a = self.join("a@example.com")
        b = self.join("b@example.com", invite=a["inviteCode"].lower(), ip="other")
        self.assertEqual(b["invite"], "counted")


class Ranking(Base):
    def test_invites_desc_then_joined_asc(self):
        a = self.join("a@example.com", ip="ia")
        b = self.join("b@example.com", ip="ib")
        c = self.join("c@example.com", ip="ic")
        self.assertEqual([self.position_of(x) for x in (a, b, c)], [1, 2, 3])
        self.join("d@example.com", invite=c["inviteCode"], ip="id")
        self.assertEqual([self.position_of(x) for x in (c, a, b)], [1, 2, 3])
        self.join("e@example.com", invite=b["inviteCode"], ip="ie")
        # b and c both have one invite; c joined later, so b is ahead of c now
        self.assertEqual([self.position_of(x) for x in (b, c, a)], [1, 2, 3])

    def test_leaderboard_size(self):
        for i in range(7):
            self.join(f"p{i}@example.com", ip=f"i{i}")
        self.assertEqual(len(self.store.leaderboard(5)), 5)
        self.assertEqual([r["position"] for r in self.store.leaderboard(5)], [1, 2, 3, 4, 5])


class OneLevel(Base):
    def test_only_direct_invites_count(self):
        a = self.join("a@example.com", ip="ia")
        b = self.join("b@example.com", invite=a["inviteCode"], ip="ib")
        c = self.join("c@example.com", invite=b["inviteCode"], ip="ic")
        self.join("d@example.com", invite=c["inviteCode"], ip="id")
        self.assertEqual(self.invites_of(a), 1)            # never b's or c's invitees
        self.assertEqual(self.invites_of(b), 1)
        self.assertEqual(self.invites_of(c), 1)

    def test_counts_once(self):
        a = self.join("a@example.com", ip="ia")
        addr = ua()
        self.join("b@example.com", invite=a["inviteCode"], ip="ib", address=addr)
        again = self.join("b@example.com", invite=a["inviteCode"], ip="ib", address=addr)
        self.assertFalse(again["created"])
        self.assertEqual(self.invites_of(a), 1)

    def test_same_network_as_inviter_does_not_count(self):
        a = self.join("a@example.com", ip="same")
        b = self.join("b@example.com", invite=a["inviteCode"], ip="same")
        self.assertEqual(b["invite"], "not-counted")
        self.assertEqual(self.invites_of(a), 0)

    def test_own_code_cannot_be_used(self):
        a = self.join("a@example.com", ip="ia")
        # a second join with the same details is the same entry, never an invite
        again = self.store.join("a@example.com", "a@example.com",
                                self.store.ranking()[0]["address"], a["inviteCode"], "zz")
        self.assertFalse(again["created"])
        self.assertEqual(self.invites_of(a), 0)


class Deleting(Base):
    def test_delete_removes_personal_data_and_the_invite(self):
        a = self.join("a@example.com", ip="ia")
        b = self.join("bee@example.com", invite=a["inviteCode"], ip="ib")
        self.assertEqual(self.invites_of(a), 1)
        self.assertTrue(self.store.delete(b["key"]))
        self.assertEqual(self.store.total(), 1)
        self.assertEqual(self.invites_of(a), 0)          # an invite that left no longer counts
        conn = sqlite3.connect(self.store.path)
        conn.execute("PRAGMA wal_checkpoint(FULL)")
        dump = "\n".join(conn.iterdump())
        conn.close()
        self.assertNotIn("bee@example.com", dump)
        self.assertIsNone(self.store.me(b["key"]))

    def test_deleting_the_inviter_detaches_the_invitee(self):
        a = self.join("a@example.com", ip="ia")
        b = self.join("b@example.com", invite=a["inviteCode"], ip="ib")
        self.assertTrue(self.store.delete(a["key"]))
        self.assertIsNotNone(self.store.me(b["key"]))
        self.assertEqual(self.store.total(), 1)

    def test_wrong_keys(self):
        self.join("a@example.com")
        for key in ("", None, "x" * 22, "y" * 200, 12):
            self.assertFalse(self.store.delete(key))
        self.assertEqual(self.store.total(), 1)

    def test_me(self):
        a = self.join("a@example.com")
        me = self.store.me(a["key"])
        self.assertEqual((me["position"], me["invites"], me["inviteCode"], me["total"]), (1, 0, a["inviteCode"], 1))
        self.assertEqual(len(me["joinedUtc"]), 10)


class MailOn(Base):
    mail_on = True

    def test_invite_counts_only_after_confirmation(self):
        a = self.join("a@example.com", ip="ia")
        b = self.join("b@example.com", invite=a["inviteCode"], ip="ib")
        self.assertEqual(b["invite"], "after-confirmation")
        self.assertTrue(b["confirmToken"])
        self.assertEqual(self.invites_of(a), 0)
        self.assertIsNone(self.store.confirm("x" * 22))
        self.assertEqual(self.store.confirm(b["confirmToken"]), 0)
        self.assertEqual(self.invites_of(a), 1)
        self.assertIsNone(self.store.confirm(b["confirmToken"]))  # used once
        self.assertTrue(self.store.me(b["key"])["confirmed"])

    def test_unconfirmed_invitee_leaving_adds_nothing(self):
        a = self.join("a@example.com", ip="ia")
        b = self.join("b@example.com", invite=a["inviteCode"], ip="ib")
        self.store.delete(b["key"])
        self.assertEqual(self.invites_of(a), 0)

    def test_confirmed_invitee_leaving_takes_the_invite_along(self):
        a = self.join("a@example.com", ip="ia")
        b = self.join("b@example.com", invite=a["inviteCode"], ip="ib")
        self.store.confirm(b["confirmToken"])
        self.assertEqual(self.invites_of(a), 1)
        self.store.delete(b["key"])
        self.assertEqual(self.invites_of(a), 0)

    def test_unconfirmed_entry_does_not_own_its_email(self):
        squatter = self.join("victim@example.com", ip="is")
        helper = self.join("h@example.com", invite=squatter["inviteCode"], ip="ih")
        self.store.confirm(helper["confirmToken"])
        self.assertEqual(self.invites_of(squatter), 1)
        owner = self.join("victim@example.com", ip="io")       # allowed: the squatter is unconfirmed
        self.assertTrue(owner["created"])
        self.assertEqual(self.store.confirm(owner["confirmToken"]), 1)   # the squatter is removed
        self.assertIsNone(self.store.me(squatter["key"]))
        self.assertTrue(self.store.me(owner["key"])["confirmed"])
        self.assertEqual(self.store.total(), 2)
        # Once confirmed, the email is owned: a further entry with it is refused.
        with self.assertRaises(Conflict):
            self.join("victim@example.com", ip="ix")

    def test_squatter_invites_are_dropped(self):
        squatter = self.join("v2@example.com", ip="is")
        helper = self.join("h2@example.com", invite=squatter["inviteCode"], ip="ih")
        self.store.confirm(helper["confirmToken"])
        owner = self.join("v2@example.com", ip="io")
        self.store.confirm(owner["confirmToken"])
        ranked = {r["id"]: r for r in self.store.ranking()}
        self.assertNotIn(squatter["id"], ranked)
        self.assertTrue(all(r["invites"] == 0 for r in ranked.values()))

    def test_unconfirmed_holder_cannot_confirm_after_the_owner(self):
        squatter = self.join("v@example.com", ip="is")
        owner = self.join("v@example.com", ip="io")
        self.store.confirm(owner["confirmToken"])
        self.assertIsNone(self.store.confirm(squatter["confirmToken"]))

    def test_token_stored_only_as_hash(self):
        b = self.join("b@example.com")
        conn = sqlite3.connect(self.store.path)
        dump = "\n".join(conn.iterdump())
        conn.close()
        self.assertNotIn(b["confirmToken"], dump)


class MailOffOwnership(Base):
    def test_first_entry_owns_the_email_while_mail_is_off(self):
        self.join("a@example.com")
        with self.assertRaises(Conflict):
            self.join("a@example.com")


class News(Base):
    def test_news_consent_is_separate_and_optional(self):
        a = self.join("a@example.com", ip="ia")
        b = self.join("b@example.com", ip="ib", news=True)
        self.assertFalse(self.store.me(a["key"])["news"])
        self.assertTrue(self.store.me(b["key"])["news"])
        conn = sqlite3.connect(self.store.path)
        stamps = dict(conn.execute("SELECT email, news_consent_utc FROM entries").fetchall())
        conn.close()
        self.assertIsNone(stamps["a@example.com"])
        self.assertTrue(stamps["b@example.com"].endswith("Z"))

    def test_stop_news(self):
        b = self.join("b@example.com", news=True)
        self.assertTrue(self.store.stop_news(b["key"]))
        self.assertFalse(self.store.me(b["key"])["news"])
        self.assertFalse(self.store.stop_news("x" * 22))

    def test_purge_without_news_consent(self):
        a = self.join("a@example.com", ip="ia")
        b = self.join("b@example.com", ip="ib", news=True)
        c = self.join("c@example.com", ip="ic")
        self.assertEqual(self.store.purge_without_news_consent("2000-01-01", dry_run=False), 0)
        self.assertEqual(self.store.purge_without_news_consent("2999-01-01"), 2)      # dry run
        self.assertEqual(self.store.total(), 3)
        self.assertEqual(self.store.purge_without_news_consent("2999-01-01", dry_run=False), 2)
        self.assertEqual(self.store.total(), 1)
        self.assertIsNone(self.store.me(a["key"]))
        self.assertIsNone(self.store.me(c["key"]))
        self.assertIsNotNone(self.store.me(b["key"]))


class Operations(Base):
    def test_secure_delete_is_on(self):
        conn = self.store.connect()
        self.assertEqual(conn.execute("PRAGMA secure_delete").fetchone()[0], 1)
        conn.close()

    def test_backup_is_consistent_and_rotates(self):
        self.join("a@example.com")
        dest = os.path.join(self.dir, "backups")
        os.makedirs(dest)
        for i in range(16):
            open(os.path.join(dest, f"waitlist-20260101T0000{i:02d}Z.sqlite3"), "w").close()
        target, removed = self.store.backup(dest, keep=14)
        self.assertEqual(len(removed), 3)
        self.assertEqual(len(os.listdir(dest)), 14)
        conn = sqlite3.connect(target)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0], 1)
        conn.close()

    def test_export(self):
        a = self.join("=cmd@example.com", ip="ia")
        self.join("b@example.com", invite=a["inviteCode"], ip="ib")
        time.sleep(0.01)
        target, count, _ = self.store.export(os.path.join(self.dir, "exports"))
        self.assertEqual(count, 2)
        with open(target, encoding="utf-8") as fh:
            rows = list(csv.reader(fh))
        self.assertEqual(rows[0], ["email", "address", "joined", "confirmed", "news_consent", "invites", "position"])
        self.assertEqual(rows[1][0], "'=cmd@example.com")   # no formula injection
        self.assertEqual((rows[1][4], rows[1][5], rows[1][6]), ("", "1", "1"))
        for _ in range(6):
            self.store.export(os.path.join(self.dir, "exports"), keep=5)
        self.assertEqual(len(os.listdir(os.path.join(self.dir, "exports"))), 5)
        if os.name == "posix":
            self.assertEqual(os.stat(target).st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
