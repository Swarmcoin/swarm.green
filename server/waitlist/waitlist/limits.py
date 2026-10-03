"""The client address, salted IP hashing and in-memory rate limits.

The client address
------------------
The service is reached only through the Vercel function
api/waitlist/[...path].js on swarm.green. That function sends the visitor's
address, as Vercel itself determined it, in X-Waitlist-Client-Ip, together with
the shared secret X-Waitlist-Proxy-Secret. web.py believes the address only
when the secret matched; X-Forwarded-For is never read. A request without a
usable address falls into one shared "unknown" bucket.

IPv6 addresses are reduced to their /64 network before hashing, because one
household or phone usually holds a whole /64.
"""
from __future__ import annotations

import collections
import hashlib
import hmac
import ipaddress
import threading
import time


def parse_client_ip(text):
    """One IP address (v4 or v6; an IPv4-mapped v6 becomes v4) or None."""
    if not isinstance(text, str):
        return None
    text = text.strip()
    if not text or len(text) > 64:
        return None
    try:
        ip = ipaddress.ip_address(text)
    except ValueError:
        return None
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return str(ip)


def ip_hash(ip, salt):
    """Salted hash of an address (IPv6: its /64). Only this is ever stored."""
    if ip is None:
        return None
    addr = ipaddress.ip_address(ip)
    if addr.version == 6:
        key = str(ipaddress.ip_network(f"{addr}/64", strict=False).network_address) + "/64"
    else:
        key = str(addr)
    return hmac.new(salt.encode("utf-8"), key.encode("ascii"), hashlib.sha256).hexdigest()[:32]


class RateLimiter:
    """Sliding windows kept in memory: a restart forgets them, which is fine
    for a waiting list. The table holds at most ``max_keys`` keys; when full,
    the key used least recently is dropped first."""

    def __init__(self, clock=time.monotonic, max_keys=50000):
        self._clock = clock
        self._lock = threading.Lock()
        self._hits = collections.OrderedDict()
        self.max_keys = max_keys

    def _queue(self, key, window, now):
        k = (key, window)
        q = self._hits.get(k)
        if q is None:
            q = collections.deque()
            self._hits[k] = q
            while len(self._hits) > self.max_keys:
                self._hits.popitem(last=False)
        else:
            self._hits.move_to_end(k)
        while q and q[0] <= now - window:
            q.popleft()
        return q

    def peek(self, rules):
        """The key of the first rule that would refuse, or None. Records nothing."""
        now = self._clock()
        with self._lock:
            for key, limit, window in rules:
                if limit > 0 and len(self._queue(key, window, now)) >= limit:
                    return key
            return None

    def record(self, rules):
        now = self._clock()
        with self._lock:
            for key, limit, window in rules:
                if limit > 0:
                    self._queue(key, window, now).append(now)

    def check(self, rules):
        """None when every rule allows (and the attempt is then recorded under
        all of them), otherwise the key of the first rule that refuses."""
        now = self._clock()
        with self._lock:
            for key, limit, window in rules:
                if limit > 0 and len(self._queue(key, window, now)) >= limit:
                    return key
            for key, limit, window in rules:
                if limit > 0:
                    self._queue(key, window, now).append(now)
            return None

    def hit(self, rules):
        return self.check(rules) is None

    def __len__(self):
        return len(self._hits)
