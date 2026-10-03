"""Settings, read once from the environment. Every name and default is listed
in DEPLOY.md. Secrets (WAITLIST_PROXY_SECRET, WAITLIST_IP_SALT, SMTP_PASSWORD)
are never logged."""
from __future__ import annotations

import os
from dataclasses import dataclass, field

MIN_SECRET = 32


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
    mode: str = "production"
    data_dir: str = "/data"
    host: str = "0.0.0.0"
    port: int = 8080
    public_base_url: str = "https://swarm.green"
    allowed_origins: list = field(default_factory=lambda: ["https://swarm.green"])
    # Shared with the Vercel function api/waitlist/[...path].js. Every route but
    # healthz needs it, and only with it is X-Waitlist-Client-Ip believed.
    proxy_secret: str = ""
    ip_salt: str = ""
    # Abuse limits on POST /join. Every attempt counts against the caller's
    # own limits; only a successful creation counts against the global one.
    join_per_ip_per_hour: int = 5
    join_per_ip_per_day: int = 20
    join_global_per_minute: int = 60
    requests_per_ip_per_minute: int = 120
    limiter_max_keys: int = 50000
    max_body_bytes: int = 4096
    read_deadline_seconds: float = 10.0
    max_workers: int = 32
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
    exports_keep: int = 5

    @property
    def mail_on(self):
        return self.mail_mode == "smtp"

    @classmethod
    def from_env(cls, env=None, require_secret=True):
        env = os.environ if env is None else env
        c = cls(
            mode=env.get("WAITLIST_MODE", "production").strip().lower() or "production",
            data_dir=env.get("WAITLIST_DATA_DIR", "/data"),
            host=env.get("WAITLIST_HOST", "0.0.0.0"),
            port=_int(env, "WAITLIST_PORT", 8080),
            public_base_url=env.get("WAITLIST_PUBLIC_BASE_URL", "https://swarm.green").rstrip("/"),
            allowed_origins=_list(env, "WAITLIST_ALLOWED_ORIGINS", ["https://swarm.green"]),
            proxy_secret=env.get("WAITLIST_PROXY_SECRET", ""),
            ip_salt=env.get("WAITLIST_IP_SALT", ""),
            join_per_ip_per_hour=_int(env, "WAITLIST_JOIN_PER_IP_PER_HOUR", 5),
            join_per_ip_per_day=_int(env, "WAITLIST_JOIN_PER_IP_PER_DAY", 20),
            join_global_per_minute=_int(env, "WAITLIST_JOIN_GLOBAL_PER_MINUTE", 60),
            requests_per_ip_per_minute=_int(env, "WAITLIST_REQUESTS_PER_IP_PER_MINUTE", 120),
            limiter_max_keys=_int(env, "WAITLIST_LIMITER_MAX_KEYS", 50000),
            read_deadline_seconds=float(env.get("WAITLIST_READ_DEADLINE_SECONDS", "") or 10),
            max_workers=_int(env, "WAITLIST_MAX_WORKERS", 32),
            mail_mode=env.get("MAIL_MODE", "off").strip().lower() or "off",
            smtp_host=env.get("SMTP_HOST", ""),
            smtp_port=_int(env, "SMTP_PORT", 587),
            smtp_user=env.get("SMTP_USER", ""),
            smtp_password=env.get("SMTP_PASSWORD", ""),
            smtp_starttls=_bool(env, "SMTP_STARTTLS", True),
            smtp_ssl=_bool(env, "SMTP_SSL", False),
            mail_from=env.get("MAIL_FROM", ""),
            exports_keep=_int(env, "WAITLIST_EXPORTS_KEEP", 5),
        )
        if c.mode not in ("production", "development"):
            raise SystemExit("WAITLIST_MODE must be production or development")
        if require_secret:
            if not c.proxy_secret:
                raise SystemExit("WAITLIST_PROXY_SECRET is not set: refusing to start")
            if c.mode == "production" and len(c.proxy_secret) < MIN_SECRET:
                raise SystemExit(f"WAITLIST_PROXY_SECRET must be at least {MIN_SECRET} characters in production")
        if c.mail_mode not in ("off", "smtp"):
            raise SystemExit("MAIL_MODE must be off or smtp")
        if c.mail_on and not (c.smtp_host and c.mail_from):
            raise SystemExit("MAIL_MODE=smtp needs SMTP_HOST and MAIL_FROM")
        if c.max_workers < 1:
            raise SystemExit("WAITLIST_MAX_WORKERS must be at least 1")
        return c
