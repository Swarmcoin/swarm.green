"""Email syntax check: a pragmatic subset of RFC 5321/5322.

Accepted: ``local@domain`` with a dot-atom local part (1-64 characters of
letters, digits and ``!#$%&'*+/=?^_`{|}~-``, dots only between characters) and
an ASCII domain of at least two labels (letters, digits and inner hyphens, each
label 1-63 characters, the last one alphabetic or ``xn--``). Quoted local
parts, comments, IP-literal domains and non-ASCII are refused: a waiting list
does not need them, and refusing them keeps the check predictable. The whole
address is lower-cased and at most 254 characters.
"""
from __future__ import annotations

import re

MAX_LEN = 254
_LOCAL = re.compile(r"^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*$")
_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
_TLD = re.compile(r"^(?:[a-z]{2,63}|xn--[a-z0-9-]{1,59})$")

MSG_EMPTY = "Enter your email address."
MSG_BAD = "This does not look like an email address. Check it for typing errors."

_GMAIL = {"gmail.com", "googlemail.com"}


class EmailError(ValueError):
    pass


def validate(value):
    if not isinstance(value, str) or not value.strip():
        raise EmailError(MSG_EMPTY)
    text = value.strip().lower()
    if len(text) > MAX_LEN or not text.isascii() or text.count("@") != 1:
        raise EmailError(MSG_BAD)
    local, domain = text.split("@")
    if not 1 <= len(local) <= 64 or not _LOCAL.match(local):
        raise EmailError(MSG_BAD)
    labels = domain.split(".")
    if len(labels) < 2 or not all(_LABEL.match(lb) for lb in labels) or not _TLD.match(labels[-1]):
        raise EmailError(MSG_BAD)
    return text


def canonical(email):
    """The mailbox behind an address, for the one-entry-per-person rule:
    a ``+tag`` is dropped everywhere, and for Gmail the dots too
    (``a.b+x@googlemail.com`` and ``ab@gmail.com`` are one mailbox)."""
    local, domain = email.split("@")
    local = local.split("+", 1)[0] or local
    if domain in _GMAIL:
        local = local.replace(".", "")
        domain = "gmail.com"
    return local + "@" + domain
