"""Settings, read once from the environment. Every name and default is listed
in DEPLOY.md; nothing here is secret except WAITLIST_IP_SALT and SMTP_PASSWORD,
which are never logged."""
from __future__ import annotations

import os
from dataclasses import dataclass, field


def _int(env, name, default):
    raw = env.get(name, "")
    try:
        return int(raw) if raw.strip() else default
    except ValueError:
        raise SystemExit(f"{name} must be a whole number")


def _bool(env, name, default):
    raw = env.get(name, "").strip().lower()
    if not raw:
        return default
    return raw in ("1", "true", "yes", "on")


def _list(env, name, default):
    raw = env.get(name)
    if raw is None or not raw.strip():
        return list(default)
    return [p.strip() for p in raw.split(",") if p.strip()]


@dataclass
class Config:
    data_dir: str = "/data"
    host: str = "0.0.0.0"
    port: int = 8080
    public_base_url: str = "https://swarm.green"
    allowed_origins: list = field(default_factory=lambda: ["https://swarm.green"])
    # Who may tell us the client address in X-Forwarded-For, and how to read it.
    trusted_proxies: list = field(default_factory=lambda: ["private_ranges"])
    client_ip_mode: str = "leftmost-public"
    ip_salt: str = ""
    # Abuse limits on POST /join, per salted IP hash and for the whole service.
    join_per_ip_per_hour: int = 5
    join_per_ip_per_day: int = 20
    join_global_per_minute: int = 60
    # Every endpoint, per salted IP hash.
    requests_per_ip_per_minute: int = 120
    max_body_bytes: int = 4096
    # Mail: off by default. In smtp mode one confirmation message per join.
    mail_mode: str = "off"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_starttls: bool = True
    smtp_ssl: bool = False
    mail_from: str = ""
    leaderboard_size: int = 50
    backups_keep: int = 14

    @property
    def mail_on(self):
        return self.mail_mode == "smtp"

    @classmethod
    def from_env(cls, env=None):
        env = os.environ if env is None else env
        c = cls(
            data_dir=env.get("WAITLIST_DATA_DIR", "/data"),
            host=env.get("WAITLIST_HOST", "0.0.0.0"),
            port=_int(env, "WAITLIST_PORT", 8080),
            public_base_url=env.get("WAITLIST_PUBLIC_BASE_URL", "https://swarm.green").rstrip("/"),
            allowed_origins=_list(env, "WAITLIST_ALLOWED_ORIGINS", ["https://swarm.green"]),
            trusted_proxies=_list(env, "WAITLIST_TRUSTED_PROXIES", ["private_ranges"]),
            client_ip_mode=env.get("WAITLIST_CLIENT_IP", "leftmost-public"),
            ip_salt=env.get("WAITLIST_IP_SALT", ""),
            join_per_ip_per_hour=_int(env, "WAITLIST_JOIN_PER_IP_PER_HOUR", 5),
            join_per_ip_per_day=_int(env, "WAITLIST_JOIN_PER_IP_PER_DAY", 20),
            join_global_per_minute=_int(env, "WAITLIST_JOIN_GLOBAL_PER_MINUTE", 60),
            requests_per_ip_per_minute=_int(env, "WAITLIST_REQUESTS_PER_IP_PER_MINUTE", 120),
            mail_mode=env.get("MAIL_MODE", "off").strip().lower() or "off",
            smtp_host=env.get("SMTP_HOST", ""),
            smtp_port=_int(env, "SMTP_PORT", 587),
            smtp_user=env.get("SMTP_USER", ""),
            smtp_password=env.get("SMTP_PASSWORD", ""),
            smtp_starttls=_bool(env, "SMTP_STARTTLS", True),
            smtp_ssl=_bool(env, "SMTP_SSL", False),
            mail_from=env.get("MAIL_FROM", ""),
        )
        if c.mail_mode not in ("off", "smtp"):
            raise SystemExit("MAIL_MODE must be off or smtp")
        if c.client_ip_mode not in ("leftmost-public", "rightmost-untrusted", "peer"):
            raise SystemExit("WAITLIST_CLIENT_IP must be leftmost-public, rightmost-untrusted or peer")
        if c.mail_on and not (c.smtp_host and c.mail_from):
            raise SystemExit("MAIL_MODE=smtp needs SMTP_HOST and MAIL_FROM")
        return c
