"""Client address behind proxies, salted IP hashing and in-memory rate limits.

The client address
------------------
Production path: browser -> Vercel (rewrite) -> the server's Caddy (two hops)
-> this container. Only a request whose direct peer is a trusted proxy
(WAITLIST_TRUSTED_PROXIES, CIDRs or the keyword ``private_ranges``) has its
X-Forwarded-For read at all; anything else is identified by its peer address.

WAITLIST_CLIENT_IP chooses how the header is read:

``leftmost-public`` (default)
    The left-most entry that is a valid public address. Vercel replaces
    X-Forwarded-For with the address it saw, and each Caddy hop appends, so
    the left-most public entry is the visitor. A request that bypasses Vercel
    and talks to Caddy directly can put anything there, so per-IP limits are
    a speed bump, not a wall; the global limit still holds.
``rightmost-untrusted``
    Walk from the right and take the first entry that is not itself a trusted
    proxy: the classic spoof-resistant reading, correct only when every hop
    (including Vercel) is listed as trusted.
``peer``
    Ignore the header.

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

PRIVATE_RANGES = ["127.0.0.0/8", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16",
                  "169.254.0.0/16", "100.64.0.0/10", "::1/128", "fc00::/7", "fe80::/10"]


def parse_networks(items):
    nets = []
    for item in items:
        if item == "private_ranges":
            nets.extend(ipaddress.ip_network(n) for n in PRIVATE_RANGES)
        else:
            nets.append(ipaddress.ip_network(item, strict=False))
    return nets


def _ip(text):
    text = (text or "").strip().strip('"')
    if text.startswith("[") and "]" in text:          # [v6]:port
        text = text[1:text.index("]")]
    elif text.count(":") == 1 and "." in text:          # v4:port
        text = text.split(":", 1)[0]
    try:
        ip = ipaddress.ip_address(text)
    except ValueError:
        return None
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return ip


def _in(ip, nets):
    return any(ip.version == n.version and ip in n for n in nets)


def client_ip(peer, xff, trusted, mode="leftmost-public"):
    """The client's address as a string, following the rules above."""
    peer_ip = _ip(peer)
    if peer_ip is None:
        return None
    if mode == "peer" or not xff or not _in(peer_ip, trusted):
        return str(peer_ip)
    chain = [_ip(p) for p in xff.split(",")]
    if mode == "leftmost-public":
        for ip in chain:
            if ip is not None and ip.is_global:
                return str(ip)
        return str(peer_ip)
    # rightmost-untrusted
    for ip in reversed(chain):
        if ip is None:
            return str(peer_ip)
        if not _in(ip, trusted):
            return str(ip)
    return str(peer_ip)


def forwarded_info(peer, xff, trusted):
    """Non-identifying facts for /healthz: was the header used, and how long it is."""
    peer_ip = _ip(peer)
    used = bool(xff) and peer_ip is not None and _in(peer_ip, trusted)
    entries = [p for p in (xff or "").split(",") if p.strip()]
    public = sum(1 for p in entries if (_ip(p) is not None and _ip(p).is_global))
    return {"forwardedHeaderUsed": used, "forwardedEntries": len(entries), "publicEntries": public}


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
    for a waiting list. ``hit`` records the attempt only when it is allowed."""

    def __init__(self, clock=time.monotonic):
        self._clock = clock
        self._lock = threading.Lock()
        self._hits = collections.defaultdict(collections.deque)
        self._last_sweep = clock()

    def hit(self, rules):
        """rules: [(key, limit, window_seconds)]. True when every rule allows."""
        return self.check(rules) is None

    def check(self, rules):
        """None when every rule allows (and the attempt is recorded under all
        of them), otherwise the key of the first rule that refuses."""
        now = self._clock()
        with self._lock:
            self._sweep(now)
            for key, limit, window in rules:
                if limit <= 0:
                    continue
                q = self._hits[(key, window)]
                while q and q[0] <= now - window:
                    q.popleft()
                if len(q) >= limit:
                    return key
            for key, limit, window in rules:
                if limit > 0:
                    self._hits[(key, window)].append(now)
            return None

    def _sweep(self, now):
        if now - self._last_sweep < 300:
            return
        self._last_sweep = now
        for (key, window), q in list(self._hits.items()):
            while q and q[0] <= now - window:
                q.popleft()
            if not q:
                del self._hits[(key, window)]
