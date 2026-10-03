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


TRUSTED = limits.parse_networks(["private_ranges"])


class ClientIp(unittest.TestCase):
    def test_untrusted_peer_header_is_ignored(self):
        self.assertEqual(limits.client_ip("8.8.4.4", "1.1.1.1", TRUSTED), "8.8.4.4")

    def test_trusted_peer_leftmost_public(self):
        # Vercel puts the visitor first; each Caddy hop appends its peer.
        self.assertEqual(limits.client_ip("172.18.0.5", "93.184.216.34, 76.76.21.21, 172.19.0.2", TRUSTED),
                         "93.184.216.34")

    def test_leftmost_skips_private_and_junk(self):
        self.assertEqual(limits.client_ip("10.0.0.2", "unknown, 192.168.1.4, 2a00:1450:4001::1, 8.8.8.8", TRUSTED),
                         "2a00:1450:4001::1")

    def test_no_public_entry_falls_back_to_peer(self):
        self.assertEqual(limits.client_ip("10.0.0.2", "192.168.1.4", TRUSTED), "10.0.0.2")

    def test_rightmost_untrusted(self):
        self.assertEqual(limits.client_ip("10.0.0.2", "1.2.3.4, 93.184.216.34, 10.0.0.9", TRUSTED,
                                          "rightmost-untrusted"), "93.184.216.34")

    def test_peer_mode(self):
        self.assertEqual(limits.client_ip("10.0.0.2", "8.8.8.8", TRUSTED, "peer"), "10.0.0.2")

    def test_ports_brackets_and_mapped(self):
        self.assertEqual(limits.client_ip("::ffff:10.0.0.2", "[2a00:1450::1]:443", TRUSTED), "2a00:1450::1")
        self.assertEqual(limits.client_ip("127.0.0.1", "8.8.8.8:5555", TRUSTED), "8.8.8.8")

    def test_custom_trusted_list(self):
        nets = limits.parse_networks(["203.0.113.0/24"])
        self.assertEqual(limits.client_ip("203.0.113.9", "8.8.8.8", nets), "8.8.8.8")
        self.assertEqual(limits.client_ip("10.0.0.1", "8.8.8.8", nets), "10.0.0.1")

    def test_forwarded_info_reveals_no_address(self):
        info = limits.forwarded_info("10.0.0.2", "8.8.8.8, 10.0.0.3", TRUSTED)
        self.assertEqual(info, {"forwardedHeaderUsed": True, "forwardedEntries": 2, "publicEntries": 1})


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

    def test_keys_are_separate(self):
        self.assertTrue(self.rl.hit([("a", 1, 60)]))
        self.assertTrue(self.rl.hit([("b", 1, 60)]))
        self.assertFalse(self.rl.hit([("a", 1, 60)]))


if __name__ == "__main__":
    unittest.main()
