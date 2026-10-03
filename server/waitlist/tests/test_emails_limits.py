import unittest

from waitlist import emails, limits


class Emails(unittest.TestCase):
    def test_valid(self):
        for raw, want in (("Bee@Example.com", "bee@example.com"), (" a.b+c@sub.example.org ", "a.b+c@sub.example.org"),
                          ("x@xn--bcher-kva.example", "x@xn--bcher-kva.example"), ("o'neil@example.ie", "o'neil@example.ie")):
            self.assertEqual(emails.validate(raw), want)

    def test_invalid(self):
        for raw in ("", None, "plain", "a@b", "a@@b.com", ".a@b.com", "a.@b.com", "a..b@c.com", "a@-b.com",
                    "a@b-.com", "a@b.c", "a@b.123", "a b@c.com", "ä@b.com", "a@[1.2.3.4]",
                    "x" * 65 + "@b.com", "a@" + "b" * 250 + ".com", '"q"@b.com', "a@b.com\n"[:-1] + " x"):
            with self.subTest(raw=raw):
                with self.assertRaises(emails.EmailError):
                    emails.validate(raw)

    def test_max_length(self):
        local = "a" * 64
        domain = ".".join(["b" * 61] * 3) + ".com"
        addr = local + "@" + domain
        self.assertLessEqual(len(addr), 254)
        self.assertEqual(emails.validate(addr), addr)

    def test_canonical(self):
        self.assertEqual(emails.canonical("a.b+news@googlemail.com"), "ab@gmail.com")
        self.assertEqual(emails.canonical("a.b+x@example.com"), "a.b@example.com")
        self.assertEqual(emails.canonical("+x@example.com"), "+x@example.com")


class ClientIp(unittest.TestCase):
    def test_parse_one_address(self):
        self.assertEqual(limits.parse_client_ip("93.184.216.34"), "93.184.216.34")
        self.assertEqual(limits.parse_client_ip(" 2a00:1450::1 "), "2a00:1450::1")
        self.assertEqual(limits.parse_client_ip("::ffff:8.8.8.8"), "8.8.8.8")

    def test_lists_ports_and_junk_are_refused(self):
        for bad in (None, "", "1.1.1.1, 8.8.8.8", "8.8.8.8:443", "[2a00::1]:443", "unknown", "x" * 100, 5):
            self.assertIsNone(limits.parse_client_ip(bad))


class IpHash(unittest.TestCase):
    def test_ipv6_same_64_same_hash(self):
        a = limits.ip_hash("2a00:1450:4001:81a::1", "salt")
        b = limits.ip_hash("2a00:1450:4001:81a:ffff::9", "salt")
        c = limits.ip_hash("2a00:1450:4001:81b::1", "salt")
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)

    def test_salt_matters_and_no_plain_ip(self):
        h1 = limits.ip_hash("8.8.8.8", "one")
        self.assertNotEqual(h1, limits.ip_hash("8.8.8.8", "two"))
        self.assertNotIn("8.8.8.8", h1)
        self.assertEqual(len(h1), 32)
        self.assertIsNone(limits.ip_hash(None, "one"))


class Limiter(unittest.TestCase):
    def setUp(self):
        self.t = 1000.0
        self.rl = limits.RateLimiter(clock=lambda: self.t)

    def test_limit_and_window(self):
        rule = [("k", 3, 60)]
        self.assertTrue(all(self.rl.hit(rule) for _ in range(3)))
        self.assertFalse(self.rl.hit(rule))
        self.t += 61
        self.assertTrue(self.rl.hit(rule))

    def test_check_names_the_refusing_rule_and_records_nothing_then(self):
        self.assertIsNone(self.rl.check([("g", 10, 60), ("ip", 1, 60)]))
        self.assertEqual(self.rl.check([("g", 10, 60), ("ip", 1, 60)]), "ip")
        # the refused attempt did not use up the global budget
        self.assertEqual(len(self.rl._hits[("g", 60)]), 1)

    def test_zero_disables_a_rule(self):
        self.assertTrue(all(self.rl.hit([("k", 0, 60)]) for _ in range(100)))

    def test_peek_records_nothing_and_record_counts(self):
        rule = [("g", 1, 60)]
        self.assertIsNone(self.rl.peek(rule))
        self.assertIsNone(self.rl.peek(rule))
        self.rl.record(rule)
        self.assertEqual(self.rl.peek(rule), "g")

    def test_table_is_bounded_and_evicts_the_oldest(self):
        rl = limits.RateLimiter(clock=lambda: self.t, max_keys=3)
        for k in ("a", "b", "c"):
            rl.hit([(k, 1, 60)])
        self.assertFalse(rl.hit([("a", 1, 60)]))   # a is used again: now the newest
        rl.hit([("d", 1, 60)])                      # evicts b, the least recently used
        self.assertEqual(len(rl), 3)
        self.assertTrue(rl.hit([("b", 1, 60)]))     # b was forgotten
        self.assertFalse(rl.hit([("d", 1, 60)]))

    def test_keys_are_separate(self):
        self.assertTrue(self.rl.hit([("a", 1, 60)]))
        self.assertTrue(self.rl.hit([("b", 1, 60)]))
        self.assertFalse(self.rl.hit([("a", 1, 60)]))


if __name__ == "__main__":
    unittest.main()
