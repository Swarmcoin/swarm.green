import os
import unittest

from waitlist import addresses as A

# The three published fund addresses and the fourth s3 address of the relaunch
# manifest (D:/privacy/network/swarm-mainnet-r2/manifest.json), the unspendable
# test address, and a public receive address from a relaunch miner kit.
S3 = ["s3fLmEHc1xqs8KAe7QS7oupkhuGDjidV4eq", "s3RiGvK5JzS8eh6ywN3K22f2LzDAhicgFuq",
      "s3g3pzQVhvVX17bzrrEN3vmcXZWSpj7KFVp", "s3R1bWZPrRCtKL122ZN6uySu1ewk2ku849C"]
S1 = "s1bbQ5zUoR3ttqKiNDVXGhy3NgoQWpWC7GL"
UA = ("swm1j77uutrvudh07mdxcynfzwxykzv3hcy2yjqn890feadhhpm35gakjp6vjcdwezg5yszkffe09zzg3vn9"
      "ulhjj8jlvhswqjlvk5c2wkxe")


def flip(text, index, alphabet):
    c = text[index]
    return text[:index] + next(a for a in alphabet if a != c) + text[index + 1:]


class Vectors(unittest.TestCase):
    def test_fund_addresses_are_p2sh(self):
        for a in S3:
            self.assertEqual(A.validate(a), (a, "p2sh"))

    def test_test_address_is_p2pkh(self):
        self.assertEqual(A.validate(S1), (S1, "p2pkh"))

    def test_unified_address(self):
        self.assertEqual(A.validate(UA), (UA, "unified"))
        self.assertEqual([t for t, _ in A.parse_unified(UA)], [0x03])  # one Orchard receiver

    def test_unified_upper_case_is_normalised(self):
        self.assertEqual(A.validate(UA.upper()), (UA, "unified"))

    def test_surrounding_space_is_trimmed(self):
        self.assertEqual(A.validate("  " + S1 + "\n")[0], S1)


class Corrupted(unittest.TestCase):
    def test_every_single_character_change_in_the_unified_address_fails(self):
        for i in range(4, len(UA)):
            with self.subTest(i=i):
                with self.assertRaises(A.AddressError) as cm:
                    A.validate(flip(UA, i, "qpzry9x8gf2tvdw0s3jn54khce6mua7l"))
                self.assertEqual(str(cm.exception), A.MSG_CHECKSUM)

    def test_single_character_changes_in_transparent_addresses_fail(self):
        for a in S3 + [S1]:
            for i in range(2, len(a)):
                with self.subTest(a=a, i=i):
                    with self.assertRaises(A.AddressError):
                        A.validate(flip(a, i, "23456789ABCDEFGH"))

    def test_checksum_message_for_transparent(self):
        with self.assertRaises(A.AddressError) as cm:
            A.validate(flip(S1, 10, "23456789ABCDEFGH"))
        self.assertEqual(str(cm.exception), A.MSG_CHECKSUM)

    def test_mixed_case_unified_fails(self):
        with self.assertRaises(A.AddressError):
            A.validate(UA[:10].upper() + UA[10:])

    def test_truncated_fails(self):
        for bad in (UA[:-1], S1[:-1], S3[0][:-3]):
            with self.assertRaises(A.AddressError):
                A.validate(bad)

    def test_bech32_not_m_fails(self):
        hrp, data = A.bech32m_decode(UA)
        values = A._hrp_expand(hrp) + data
        poly = A._polymod(values + [0] * 6) ^ 1  # Bech32 (BIP 173) constant
        bech32 = hrp + "1" + "".join(A._CHARSET[d] for d in data + [(poly >> 5 * (5 - i)) & 31 for i in range(6)])
        with self.assertRaises(A.AddressError):
            A.validate(bech32)


class OtherNetworks(unittest.TestCase):
    def test_testnet_is_refused_with_its_own_message(self):
        fake = A.bech32m_encode("swarm", [1] * 60)
        with self.assertRaises(A.AddressError) as cm:
            A.validate(fake)
        self.assertEqual(str(cm.exception), A.MSG_TESTNET)

    def test_foreign_base58_versions_are_refused(self):
        for version in (bytes([0x1C, 0xB8]), bytes([0x1C, 0xBD]), bytes([0x1D, 0x25]), bytes([0x1C, 0x29])):
            addr = A.b58check_encode(version + os.urandom(20))
            with self.subTest(addr=addr):
                with self.assertRaises(A.AddressError) as cm:
                    A.validate(addr)
                self.assertIn(str(cm.exception), (A.MSG_OTHER,))

    def test_other_hrp_with_valid_checksum_is_refused(self):
        with self.assertRaises(A.AddressError) as cm:
            A.validate(A.bech32m_encode("u", [3] * 80))
        self.assertEqual(str(cm.exception), A.MSG_OTHER)

    def test_empty_and_junk(self):
        for bad, msg in (("", A.MSG_EMPTY), (None, A.MSG_EMPTY), ("hello", A.MSG_OTHER),
                         ("s1 abc", A.MSG_OTHER), ("x" * 600, A.MSG_OTHER)):
            with self.assertRaises(A.AddressError) as cm:
                A.validate(bad)
            self.assertEqual(str(cm.exception), msg)


class UnifiedStructure(unittest.TestCase):
    def test_f4jumble_round_trip(self):
        for n in (48, 64, 100, 128, 200, 500):
            m = os.urandom(n)
            self.assertEqual(A.f4jumble_inv(A.f4jumble(m)), m)
            self.assertNotEqual(A.f4jumble(m), m)

    def test_sapling_and_orchard(self):
        ua = A.encode_unified([(0x02, os.urandom(43)), (0x03, os.urandom(43))])
        self.assertEqual(A.validate(ua)[1], "unified")

    def test_transparent_only_unified_is_refused(self):
        with self.assertRaises(A.AddressError):
            A.validate(A.encode_unified([(0x00, os.urandom(20))]))

    def test_unsorted_or_duplicate_typecodes_are_refused(self):
        for items in ([(0x03, os.urandom(43)), (0x02, os.urandom(43))],
                      [(0x03, os.urandom(43)), (0x03, os.urandom(43))]):
            with self.assertRaises(A.AddressError):
                A.validate(A.encode_unified(items))

    def test_p2pkh_and_p2sh_together_are_refused(self):
        with self.assertRaises(A.AddressError):
            A.validate(A.encode_unified([(0, os.urandom(20)), (1, os.urandom(20)), (3, os.urandom(43))]))

    def test_wrong_receiver_length_is_refused(self):
        with self.assertRaises(A.AddressError):
            A.validate(A.encode_unified([(0x03, os.urandom(42))]))

    def test_wrong_padding_is_refused(self):
        body = bytes([0x03, 43]) + os.urandom(43)
        raw = A.f4jumble(body + b"swarm".ljust(16, b"\0"))
        ua = A.bech32m_encode("swm", A.convertbits(raw, 8, 5, True))
        with self.assertRaises(A.AddressError) as cm:
            A.validate(ua)
        self.assertEqual(str(cm.exception), A.MSG_CHECKSUM)

    def test_unknown_typecode_is_tolerated_beside_a_shielded_receiver(self):
        ua = A.encode_unified([(0x03, os.urandom(43)), (0x10, os.urandom(5))])
        self.assertEqual(A.validate(ua)[1], "unified")


class Mask(unittest.TestCase):
    def test_mask(self):
        self.assertEqual(A.mask(UA), "swm1j77u\u2026wkxe")
        self.assertEqual(A.mask(S1), "s1bbQ5zU\u2026C7GL")


if __name__ == "__main__":
    unittest.main()
