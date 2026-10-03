"""Command line: python -m waitlist <command>

  serve        apply migrations, then serve on WAITLIST_HOST:WAITLIST_PORT
               (refuses to start without WAITLIST_PROXY_SECRET; production
               mode needs at least 32 characters)
  migrate      apply migrations and exit
  backup       consistent copy to $WAITLIST_DATA_DIR/backups, keep the newest 14
  export       CSV (email, address, joined, confirmed, news_consent, invites,
               position) to $WAITLIST_DATA_DIR/exports, mode 0600, newest 5 kept;
               prints only the path and count
  purge --without-news-consent --before YYYY-MM-DD [--yes]
               delete entries WITHOUT project-news consent that joined before
               the date; without --yes it only counts them (dry run)
  healthcheck  exit 0 when GET /waitlist/api/healthz answers on localhost (Docker HEALTHCHECK)
"""
from __future__ import annotations

import argparse
import datetime as dt
import logging
import os
import signal
import sys
import urllib.request

from .config import Config
from .web import App, make_server


def _purge(app, args):
    p = argparse.ArgumentParser(prog="python -m waitlist purge")
    p.add_argument("--without-news-consent", action="store_true", required=True,
                   help="the only purge there is: entries without project-news consent")
    p.add_argument("--before", required=True, help="UTC date YYYY-MM-DD: entries that joined before it")
    p.add_argument("--yes", action="store_true", help="really delete (default: dry run, count only)")
    a = p.parse_args(args)
    try:
        day = dt.date.fromisoformat(a.before)
    except ValueError:
        p.error("--before must be a date, YYYY-MM-DD")
    n = app.store.purge_without_news_consent(day.isoformat(), dry_run=not a.yes)
    if a.yes:
        app.invalidate()
        print(f"purge: deleted {n} entries without news consent that joined before {day.isoformat()}")
    else:
        print(f"purge (dry run): {n} entries without news consent joined before {day.isoformat()}; "
              "add --yes to delete them")
    return 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    cmd = argv[0] if argv else "serve"
    logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    cfg = Config.from_env(require_secret=(cmd == "serve"))

    if cmd == "healthcheck":
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{cfg.port}/waitlist/api/healthz", timeout=4) as r:
                return 0 if r.status == 200 else 1
        except Exception:
            return 1

    app = App(cfg)
    applied = app.store.migrate()
    if applied:
        logging.getLogger("waitlist").info("migrations applied: %s", ",".join(applied))

    if cmd == "migrate":
        return 0
    if cmd == "backup":
        target, removed = app.store.backup(os.path.join(cfg.data_dir, "backups"), cfg.backups_keep)
        print(f"backup written: {target} (rotated away: {len(removed)})")
        return 0
    if cmd == "export":
        target, count, removed = app.store.export(os.path.join(cfg.data_dir, "exports"), cfg.exports_keep)
        print(f"export written: {target} ({count} entries, mode 0600; older exports removed: {len(removed)})")
        return 0
    if cmd == "purge":
        return _purge(app, argv[1:])
    if cmd != "serve":
        print(__doc__, file=sys.stderr)
        return 2

    server = make_server(app)

    def stop(*_):
        raise KeyboardInterrupt()

    signal.signal(signal.SIGTERM, stop)
    logging.getLogger("waitlist").info("listening on %s:%s, mail %s, %s mode", cfg.host, cfg.port,
                                       cfg.mail_mode, cfg.mode)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
