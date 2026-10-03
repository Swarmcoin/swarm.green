# SWARM waiting list: Python 3.12 standard library only, one process, port 8080.
# Runs as an unprivileged user with a read-only root filesystem; everything it
# writes (database, IP salt, backups, exports) lives in the /data volume.
# Pin the base image by digest on the server before building (DEPLOY.md, step 2).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    WAITLIST_DATA_DIR=/data \
    WAITLIST_HOST=0.0.0.0 \
    WAITLIST_PORT=8080 \
    MAIL_MODE=off

RUN groupadd --system --gid 10001 waitlist \
 && useradd --system --uid 10001 --gid waitlist --no-create-home --home-dir /nonexistent --shell /usr/sbin/nologin waitlist \
 && mkdir -p /data \
 && chown waitlist:waitlist /data \
 && chmod 0700 /data

WORKDIR /app
COPY --chown=root:root waitlist /app/waitlist
COPY --chown=root:root migrations /app/migrations

USER waitlist
VOLUME ["/data"]
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD ["python", "-m", "waitlist", "healthcheck"]
CMD ["python", "-m", "waitlist", "serve"]
