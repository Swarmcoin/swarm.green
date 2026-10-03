# SWARM waiting list: Python 3.12 standard library only, one process, port 8080.
# Runs as an unprivileged user with a read-only root filesystem; everything it
# writes (database, IP salt, backups, exports) lives in the /data volume.
#
# REQUIRED: the base image is pinned by digest, and the build refuses anything
# else. No digest is written here because none could be verified offline when
# this file was written (2026-10-03). Get it on the server (DEPLOY.md, step 2):
#   docker pull python:3.12-slim
#   docker image inspect python:3.12-slim -f '{{index .RepoDigests 0}}'
# and build with
#   docker build --build-arg PYTHON_IMAGE=python:3.12-slim@sha256:<digest> -t swarm-waitlist:0.2.0 .
ARG PYTHON_IMAGE=REQUIRED-pin-python-3.12-slim-by-digest
FROM ${PYTHON_IMAGE}
ARG PYTHON_IMAGE
RUN case "${PYTHON_IMAGE}" in \
      python:3.12-slim@sha256:????????????????????????????????????????????????????????????????) ;; \
      *) echo "PYTHON_IMAGE must be python:3.12-slim@sha256:<64 hex>, see DEPLOY.md step 2" >&2; exit 1 ;; \
    esac

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    WAITLIST_DATA_DIR=/data \
    WAITLIST_HOST=0.0.0.0 \
    WAITLIST_PORT=8080 \
    WAITLIST_MODE=production \
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
