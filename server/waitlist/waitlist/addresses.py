"""SWARM mainnet address validation, standard library only.

What is verified, exactly:

Unified address (``swm1...``)
  * Bech32m (BIP 350) with the human-readable part ``swm``: character set,
    no mixed case, and the Bech32m checksum.
  * The 5-bit to 8-bit regrouping leaves no non-zero padding bits.
  * F4Jumble is undone (ZIP 316, BLAKE2b personalisations ``UA_F4Jumble_H`` /
    ``UA_F4Jumble_G``) and the last 16 bytes must be the padding ZIP 316
    prescribes: the HRP ``swm`` followed by zero bytes. A single wrong
    character anywhere fails this check as well as the checksum.
  * The receiver list parses completely (CompactSize typecode and length),
    typecodes are strictly ascending (no duplicates), P2PKH and P2SH do not
    both appear, the known receivers have their exact lengths (P2PKH 20,
    P2SH 20, Sapling 43, Orchard 43), and at least one shielded receiver
    (Sapling or Orchard) is present.
  NOT verified: that the Sapling diversified transmission key or the Orchard
  receiver is a valid curve point. A wallet would reject such an address when
  paying it; for a waiting list the checks above are enough to catch typing
  and copy errors.

Transparent address (``s1...`` / ``s3...``)
  * Base58Check: alphabet, total length 26 bytes (2 version bytes, 20-byte
    hash, 4-byte checksum) and the double-SHA-256 checksum.
  * Version bytes 0x1c28 (P2PKH, ``s1``) or 0x1c2d (P2SH, ``s3``), the
    SwarmMainnet values.

Everything else, including the testnet's ``swarm1...``, is rejected with a
message that says what a mainnet address looks like.
"""
from __future__ import annotations

import hashlib

HRP = "swm"
TESTNET_PREFIX = "swarm1"
P2PKH_VERSION = bytes([0x1C, 0x28])
P2SH_VERSION = bytes([0x1C, 0x2D])

_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
_CHARSET_REV = {c: i for i, c in enumerate(_CHARSET)}
_BECH32M_CONST = 0x2BC830A3
_B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_B58_REV = {c: i for i, c in enumerate(_B58)}

MAX_LEN = 512  # far above any real unified address; keeps the work bounded

MSG_EMPTY = "Enter your SWARM address."
MSG_TESTNET = ("This is a testnet address (it starts with swarm1). The waiting list needs a "
               "mainnet address: it starts with swm1, s1 or s3.")
MSG_CHECKSUM = ("This SWARM address has a typing error: its checksum does not match. "
                "Copy it from your wallet again.")
MSG_OTHER = ("This is not a SWARM mainnet address. Mainnet addresses start with swm1 "
             "(shielded) or s1 / s3 (transparent).")


class AddressError(ValueError):
    """Raised with a message that can be shown to the person as it is."""


# ---------------------------------------------------------------- Bech32m
def _polymod(values):
    gen = (0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3)
    chk = 1
    for v in values:
        top = chk >> 25
        chk = (chk & 0x1FFFFFF) << 5 ^ v
        for i in range(5):
            chk ^= gen[i] if ((top >> i) & 1) else 0
    return chk


def _hrp_expand(hrp):
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]


def bech32m_decode(text):
    """(hrp, 5-bit data without checksum). No length limit (unified addresses
    are longer than BIP 173's 90 characters, which ZIP 316 allows)."""
    if text != text.lower() and text != text.upper():
        raise AddressError(MSG_CHECKSUM)
    text = text.lower()
    pos = text.rfind("1")
    if pos < 1 or pos + 7 > len(text):
        raise AddressError(MSG_OTHER)
    hrp, data_part = text[:pos], text[pos + 1:]
    if any(ord(c) < 33 or ord(c) > 126 for c in hrp):
        raise AddressError(MSG_OTHER)
    try:
        data = [_CHARSET_REV[c] for c in data_part]
    except KeyError:
        raise AddressError(MSG_CHECKSUM) from None
    if _polymod(_hrp_expand(hrp) + data) != _BECH32M_CONST:
        raise AddressError(MSG_CHECKSUM)
    return hrp, data[:-6]


def bech32m_encode(hrp, data5):
    values = _hrp_expand(hrp) + list(data5)
    poly = _polymod(values + [0] * 6) ^ _BECH32M_CONST
    checksum = [(poly >> 5 * (5 - i)) & 31 for i in range(6)]
    return hrp + "1" + "".join(_CHARSET[d] for d in list(data5) + checksum)


def convertbits(data, frombits, tobits, pad):
    acc = 0
    bits = 0
    out = []
    maxv = (1 << tobits) - 1
    for value in data:
        if value < 0 or value >> frombits:
            raise AddressError(MSG_OTHER)
        acc = (acc << frombits) | value
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            out.append((acc >> bits) & maxv)
    if pad:
        if bits:
            out.append((acc << (tobits - bits)) & maxv)
    elif bits >= frombits or ((acc << (tobits - bits)) & maxv):
        raise AddressError(MSG_CHECKSUM)
    return out


# ---------------------------------------------------------------- F4Jumble (ZIP 316)
_L_H = 64


def _h(i, u, length):
    person = b"UA_F4Jumble_H" + bytes([i, 0, 0])
    return hashlib.blake2b(u, digest_size=length, person=person).digest()


def _g(i, u, length):
    out = bytearray()
    j = 0
    while len(out) < length:
        person = b"UA_F4Jumble_G" + bytes([i]) + j.to_bytes(2, "little")
        out += hashlib.blake2b(u, digest_size=64, person=person).digest()
        j += 1
    return bytes(out[:length])


def _xor(a, b):
    return bytes(x ^ y for x, y in zip(a, b))


def _split(msg):
    if not 48 <= len(msg) <= 4194368:
        raise AddressError(MSG_OTHER)
    l_l = min(_L_H, len(msg) // 2)
    return l_l, len(msg) - l_l


def f4jumble(msg):
    l_l, l_r = _split(msg)
    a, b = msg[:l_l], msg[l_l:]
    x = _xor(b, _g(0, a, l_r))
    y = _xor(a, _h(0, x, l_l))
    d = _xor(x, _g(1, y, l_r))
    c = _xor(y, _h(1, d, l_l))
    return c + d


def f4jumble_inv(msg):
    l_l, l_r = _split(msg)
    c, d = msg[:l_l], msg[l_l:]
    y = _xor(c, _h(1, d, l_l))
    x = _xor(d, _g(1, y, l_r))
    a = _xor(y, _h(0, x, l_l))
    b = _xor(x, _g(0, a, l_r))
    return a + b


# ---------------------------------------------------------------- unified address
_KNOWN_LENGTHS = {0x00: 20, 0x01: 20, 0x02: 43, 0x03: 43}
_SHIELDED = {0x02, 0x03}


def _compact_size(buf, i):
    if i >= len(buf):
        raise AddressError(MSG_OTHER)
    first = buf[i]
    if first < 0xFD:
        return first, i + 1
    width = {0xFD: 2, 0xFE: 4, 0xFF: 8}[first]
    if i + 1 + width > len(buf):
        raise AddressError(MSG_OTHER)
    value = int.from_bytes(buf[i + 1:i + 1 + width], "little")
    if value < {2: 0xFD, 4: 0x10000, 8: 0x100000000}[width]:
        raise AddressError(MSG_OTHER)  # not the canonical encoding
    return value, i + 1 + width


def parse_unified(text):
    """Returns the list of (typecode, receiver bytes) of a valid SWARM mainnet
    unified address, or raises AddressError."""
    hrp, data5 = bech32m_decode(text)
    if hrp != HRP:
        raise AddressError(MSG_OTHER)
    raw = bytes(convertbits(data5, 5, 8, False))
    plain = f4jumble_inv(raw)
    padding = HRP.encode("ascii").ljust(16, b"\0")
    if plain[-16:] != padding:
        raise AddressError(MSG_CHECKSUM)
    body = plain[:-16]
    items = []
    i = 0
    while i < len(body):
        typecode, i = _compact_size(body, i)
        length, i = _compact_size(body, i)
        if i + length > len(body):
            raise AddressError(MSG_OTHER)
        items.append((typecode, body[i:i + length]))
        i += length
    codes = [t for t, _ in items]
    if not items or codes != sorted(set(codes)):
        raise AddressError(MSG_OTHER)
    if 0x00 in codes and 0x01 in codes:
        raise AddressError(MSG_OTHER)
    for t, value in items:
        if t in _KNOWN_LENGTHS and len(value) != _KNOWN_LENGTHS[t]:
            raise AddressError(MSG_OTHER)
    if not _SHIELDED & set(codes):
        raise AddressError(MSG_OTHER)
    return items


def encode_unified(items):
    """Test helper: the inverse of parse_unified."""
    body = b""
    for t, value in items:
        body += bytes([t, len(value)]) + value
    raw = f4jumble(body + HRP.encode("ascii").ljust(16, b"\0"))
    return bech32m_encode(HRP, convertbits(raw, 8, 5, True))


# ---------------------------------------------------------------- Base58Check
def b58decode(text):
    n = 0
    for c in text:
        if c not in _B58_REV:
            raise AddressError(MSG_OTHER)
        n = n * 58 + _B58_REV[c]
    full = n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
    pad = len(text) - len(text.lstrip("1"))
    return b"\0" * pad + full


def b58encode(raw):
    n = int.from_bytes(raw, "big")
    out = ""
    while n:
        n, r = divmod(n, 58)
        out = _B58[r] + out
    pad = len(raw) - len(raw.lstrip(b"\0"))
    return "1" * pad + out


def _dsha(b):
    return hashlib.sha256(hashlib.sha256(b).digest()).digest()


def b58check_encode(payload):
    return b58encode(payload + _dsha(payload)[:4])


def parse_transparent(text):
    """Returns ('p2pkh' | 'p2sh', 20-byte hash) or raises AddressError."""
    raw = b58decode(text)
    if len(raw) != 26:
        raise AddressError(MSG_OTHER if len(text) < 30 or len(text) > 40 else MSG_CHECKSUM)
    payload, checksum = raw[:-4], raw[-4:]
    if _dsha(payload)[:4] != checksum:
        raise AddressError(MSG_CHECKSUM)
    version = payload[:2]
    if version == P2PKH_VERSION:
        return "p2pkh", payload[2:]
    if version == P2SH_VERSION:
        return "p2sh", payload[2:]
    raise AddressError(MSG_OTHER)


# ---------------------------------------------------------------- entry point
def validate(value):
    """Normalised address (unified addresses lower-cased) and its kind:
    'unified', 'p2pkh' or 'p2sh'. Raises AddressError with a readable message."""
    if not isinstance(value, str):
        raise AddressError(MSG_EMPTY)
    text = value.strip()
    if not text:
        raise AddressError(MSG_EMPTY)
    if len(text) > MAX_LEN or any(c.isspace() for c in text):
        raise AddressError(MSG_OTHER)
    low = text.lower()
    if low.startswith(TESTNET_PREFIX):
        raise AddressError(MSG_TESTNET)
    if low.startswith(HRP + "1"):
        parse_unified(text)
        return low, "unified"
    if text[:2] in ("s1", "s3"):
        kind, _ = parse_transparent(text)
        if (kind == "p2pkh") != (text[:2] == "s1"):
            raise AddressError(MSG_OTHER)
        return text, kind
    raise AddressError(MSG_OTHER)


def mask(address):
    """The public label on the leaderboard: first 8 and last 4 characters."""
    return address[:8] + "…" + address[-4:]
