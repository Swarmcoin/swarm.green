"""Command line: python -m waitlist <serve|migrate|backup|export|healthcheck>

  serve        apply migrations, then serve on WAITLIST_HOST:WAITLIST_PORT
  migrate      apply migrations and exit
  backup       consistent copy to $WAITLIST_DATA_DIR/backups, keep the newest 14
  export       CSV (email, address, joined, confirmed, invites, position) to
               $WAITLIST_DATA_DIR/exports, mode 0600; prints only the path and count
  healthcheck  exit 0 when GET /waitlist/api/healthz answers on localhost (Docker HEALTHCHECK)
"""
from __future__ import annotations

import logging
import os
import signal
import sys
import urllib.request

from .config import Config
from .web import App, make_server


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    cmd = argv[0] if argv else "serve"
    logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    cfg = Config.from_env()

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
        target, count = app.store.export(os.path.join(cfg.data_dir, "exports"))
        print(f"export written: {target} ({count} entries, mode 0600)")
        return 0
    if cmd != "serve":
        print(__doc__, file=sys.stderr)
        return 2

    server = make_server(app)
    def stop(*_):
        raise KeyboardInterrupt()

    signal.signal(signal.SIGTERM, stop)
    logging.getLogger("waitlist").info("listening on %s:%s, mail %s", cfg.host, cfg.port, cfg.mail_mode)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
