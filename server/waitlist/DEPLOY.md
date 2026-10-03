# Waiting list service: deployment (written, not executed)

The waiting list for public mining (`/waitlist` on swarm.green) talks to this
service. It is Python 3.12 standard library only (no packages), one process,
SQLite in WAL mode in the `/data` volume. Nothing here has been run on a
server; every step needs the owner's go and is the planner's to execute.

Request path in production:

```
browser ── https://swarm.green/api/waitlist/X          (same origin; CSP connect-src 'self')
   └─ Vercel function api/waitlist/[...path].js        (Node runtime, no dependencies)
        adds X-Waitlist-Proxy-Secret  = WAITLIST_PROXY_SECRET
             X-Waitlist-Client-Ip     = first entry of Vercel's own x-forwarded-for
        └─ https://lwd-main.swarm.green/waitlist/api/X
             └─ Messenger edge Caddy (TLS) ── main-web Caddy (http :8080, site lwd-main)
                  └─ handle /waitlist/api/*  ── reverse_proxy waitlist:8080
```

Every route except `healthz` answers 403 without the secret, so calling
`lwd-main` directly gets nowhere. The client address is taken only from
`X-Waitlist-Client-Ip` on a request that carried the secret; `X-Forwarded-For`
is never read, so the Caddy hops need no header changes.

Why `x-forwarded-for` in the function: Vercel's request-header documentation
(read 2026-10-03, vercel.com/docs/headers/request-headers) states that Vercel
overwrites `x-forwarded-for` with the client's public IP and does not forward
external values, to prevent spoofing. It makes that statement for this header;
`x-real-ip` / `x-vercel-forwarded-for` carry the same address without it.

## Endpoints

All under `/waitlist/api/`, JSON in and out, no CORS headers.

| Method | Path | What |
| --- | --- | --- |
| POST | `join` | `{email, address, invite?, consent: true, news?: true, trap: ""}` → 201 `{created, position, total, invites, inviteCode, inviteUrl, invite, confirmed, news, mail, inviteRule, key}`. The same email + address again → 200 `{alreadyJoined: true, position}` only. Email or address already used with a different partner → 409 `{"error": "These details cannot be added to the list."}` |
| GET | `stats` | `{total, updatedUtc}`, `Cache-Control: public, max-age=30` |
| GET | `leaderboard` | top 50 `{rank, label, invites, joinedUtc}`, label = first 8 + `…` + last 4 of the address; 30 s |
| GET / POST | `me` | `?key=` or `{key}` → own position, invites, invite link, news flag (the page uses POST) |
| POST | `delete` | `{key}` → removes the entry and its personal data; an invite it was counted as stops counting |
| POST | `news` | `{key, news: false}` → withdraws the optional project-news consent; the entry stays |
| GET / POST | `confirm` | `?token=` or `{token}`; only when `MAIL_MODE=smtp`. The first entry confirmed for an email keeps it; other unconfirmed entries with that email are removed with their invites |
| GET | `healthz` | `{ok, mail}`; open (Docker healthcheck), says nothing about clients |

## Settings (environment)

| Variable | Default | Meaning |
| --- | --- | --- |
| `WAITLIST_PROXY_SECRET` | none | **required**; same value as the Vercel production variable. `serve` refuses to start without it, and in production mode if it is shorter than 32 characters |
| `WAITLIST_MODE` | `production` | `development` only relaxes the secret's length (local tests) |
| `WAITLIST_DATA_DIR` | `/data` | `waitlist.sqlite3`, `ip-salt`, `backups/`, `exports/` |
| `WAITLIST_PORT` | `8080` | |
| `WAITLIST_PUBLIC_BASE_URL` | `https://swarm.green` | invite links and mail links |
| `WAITLIST_ALLOWED_ORIGINS` | `https://swarm.green` | a POST with any other `Origin` gets 403 |
| `WAITLIST_IP_SALT` | generated | secret for the IP hash; if unset, generated at first start into `/data/ip-salt` (0600). Set it in the env file so it survives a lost volume |
| `WAITLIST_JOIN_PER_IP_PER_HOUR` / `_PER_DAY` | `5` / `20` | every join attempt (also invalid ones) per IP hash |
| `WAITLIST_JOIN_GLOBAL_PER_MINUTE` | `60` | entries actually created, all callers together; checked after validation |
| `WAITLIST_REQUESTS_PER_IP_PER_MINUTE` | `120` | every route except healthz |
| `WAITLIST_LIMITER_MAX_KEYS` | `50000` | size cap of the in-memory limiter table; least recently used keys go first |
| `WAITLIST_READ_DEADLINE_SECONDS` | `10` | total time for request line, headers and body; then the connection is closed |
| `WAITLIST_MAX_WORKERS` | `32` | requests handled at once; beyond that an immediate 503. Keep below the container's `pids_limit` (64) |
| `WAITLIST_EXPORTS_KEEP` | `5` | newest CSV exports kept |
| `MAIL_MODE` | `off` | `off` sends nothing; `smtp` sends one confirmation mail per new entry |
| `SMTP_HOST`, `SMTP_PORT` (587), `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_STARTTLS` (true), `SMTP_SSL` (false), `MAIL_FROM` | | smtp mode only; never logged |

Body limit 4096 bytes. IPv6 addresses are hashed by their /64.

## Limits that remain (say them plainly)

- **While mail is off, membership of an email can be probed and an email can
  be occupied by a stranger.** Anyone who types an email plus an address that
  is not yet on the list learns from 201 vs 409 whether that email (or that
  address) is already used, and anyone can take an email they do not own until
  confirmation is switched on. With `MAIL_MODE=smtp`, an unconfirmed entry no
  longer owns its email: the real owner joins with their own address,
  confirms, and the stranger's entry is removed with its invites.
- **An address can be occupied by a stranger in either mode**, because nothing
  proves ownership of a SWARM address until "sign in with wallet" exists. The
  real owner then gets the neutral 409 and must write to the contact address.
- Rate limits live in memory and reset on restart.
- Several people behind one connection (household, carrier NAT) share the
  per-IP limits and cannot count as each other's invites.

## 1. Secret (planner, once)

Generate it on a trusted machine, never print it into a log or the vault:

```sh
openssl rand -base64 48 | tr -d '\n/+=' | cut -c1-48     # 48 characters
```

Put the same value in two places: the server's `waitlist.env` (step 3) and the
Vercel project's **production** environment variable `WAITLIST_PROXY_SECRET`
(Vercel dashboard or `vercel env add WAITLIST_PROXY_SECRET production`). A
redeploy of the site is needed after adding the Vercel variable. Preview
deployments get no value, so their function answers 503.

## 2. Build the image (server)

Copy `server/waitlist/` to `/opt/swarm-mainnet/waitlist/` (root, 0755/0644).

**REQUIRED, digest pin:** the Dockerfile refuses to build unless
`PYTHON_IMAGE` is `python:3.12-slim@sha256:<64 hex>`. No digest is written
into the repository because none could be verified offline when this was
written; take it on the server:

```sh
cd /opt/swarm-mainnet/waitlist
sudo docker pull python:3.12-slim
DIGEST=$(sudo docker image inspect python:3.12-slim -f '{{index .RepoDigests 0}}')   # python@sha256:…
echo "$DIGEST"        # record it in the vault (public value)
sudo docker build --build-arg PYTHON_IMAGE="python:3.12-slim@${DIGEST#*@}" -t swarm-waitlist:0.2.0 .
sudo docker run --rm --read-only --tmpfs /tmp -e WAITLIST_DATA_DIR=/tmp/t swarm-waitlist:0.2.0 \
  python -c "import waitlist.addresses as a; print(a.validate('s1bbQ5zUoR3ttqKiNDVXGhy3NgoQWpWC7GL'))"
```

Go: the last line prints `('s1bbQ5zUoR3ttqKiNDVXGhy3NgoQWpWC7GL', 'p2pkh')`.

## 3. Env file (server)

```sh
sudo install -m 0600 -o root -g root /dev/null /opt/swarm-mainnet/waitlist.env
sudo sh -c 'printf "WAITLIST_IP_SALT=%s\n" "$(openssl rand -hex 32)" >> /opt/swarm-mainnet/waitlist.env'
sudo sh -c 'printf "WAITLIST_PROXY_SECRET=%s\n" "<the secret from step 1>" >> /opt/swarm-mainnet/waitlist.env'   # type it, do not echo it elsewhere
sudo sh -c 'cat >> /opt/swarm-mainnet/waitlist.env' <<'EOF'
WAITLIST_MODE=production
WAITLIST_PUBLIC_BASE_URL=https://swarm.green
WAITLIST_ALLOWED_ORIGINS=https://swarm.green
MAIL_MODE=off
EOF
```

Never print the file (salt and secret).

## 4. Compose service (`/opt/swarm-mainnet/docker-compose.yml`)

Under `services:`:

```yaml
  waitlist:
    image: swarm-waitlist:0.2.0
    restart: unless-stopped
    env_file: ./waitlist.env
    networks: [default]          # default only; main-web reaches it as waitlist:8080
    # no ports: nothing is published on the host
    volumes:
      - waitlist:/data
    read_only: true
    tmpfs: [/tmp]
    cap_drop: [ALL]
    security_opt: ["no-new-privileges:true"]
    mem_limit: 128m
    cpus: 0.25
    pids_limit: 64               # WAITLIST_MAX_WORKERS (32) stays below it
    logging:
      driver: json-file
      options: { max-size: "10m", max-file: "3" }
```

Under the top-level `volumes:`:

```yaml
  waitlist:
    name: swarm-mainnet-waitlist
```

Check: `sudo docker compose --project-directory /opt/swarm-mainnet --env-file /opt/swarm-mainnet/.env -f /opt/swarm-mainnet/docker-compose.yml config` exits 0, `waitlist` has no `ports`, and `10.88.0.1:28233` is still the project's only published port.
Start only this service: `sudo docker compose … up -d waitlist`; `ps waitlist` → `healthy` within a minute.

## 5. Caddy (`/opt/swarm-mainnet/config/Caddyfile.main-web`)

Inside the `http://{$SWARM_MAIN_LWD_DOMAIN}:8080` site, **before** the gRPC
catch-all handle (the `(swarm_lightwallet)` import):

```caddy
	handle /waitlist/api/* {
		request_body {
			max_size 8KB
		}
		reverse_proxy waitlist:8080 {
			request_buffers 8KB
		}
	}
```

`request_buffers` makes Caddy read the (small) body before it opens the
upstream request, so a slow client holds a Caddy buffer, not one of the
service's 32 workers; the service still enforces its own 10-second deadline and
4 KB limit. `handle` does not strip the prefix. No header changes anywhere: the
service ignores `X-Forwarded-For`. The edge (Messenger) Caddy needs nothing.

Validate, then reload:

```sh
sudo docker run --rm -v /opt/swarm-mainnet/config/Caddyfile.main-web:/etc/caddy/Caddyfile:ro \
  -e SWARM_MAIN_LWD_DOMAIN=lwd-main.swarm.green -e SWARM_ZAINO_GRPC_PORT=9068 \
  -e SWARM_EXPLORER_PORT=4000 -e SWARM_HSTS_MAX_AGE=31536000 \
  caddy:2.11-alpine caddy validate --config /etc/caddy/Caddyfile
sudo docker compose … exec main-web caddy reload --config /etc/caddy/Caddyfile
```

## 6. Test (after the site deploy with the Vercel variable)

```sh
curl -s https://lwd-main.swarm.green/waitlist/api/healthz    # {"ok":true,"mail":"off"}
curl -s https://lwd-main.swarm.green/waitlist/api/stats      # {"error":"Forbidden."} (403): direct access is closed
curl -s https://swarm.green/api/waitlist/stats               # {"total":0,...} through the function
```

CHECK on the first Vercel deployment: `GET /api/waitlist/stats` answers JSON
from the function (Vercel routes `api/waitlist/[...path].js` for every path
under `/api/waitlist/`). If it answers 404, add to `vercel.json` rewrites
`{ "source": "/api/waitlist/:path*", "destination": "/api/waitlist/[...path]?path=:path*" }`;
the function reads the route from the path or from `?path=`.

One end-to-end join with a test address is the owner's call (it puts a real
entry on the public list; remove it afterwards with "Remove me").

## 7. Backups, export, purge

```sh
sudo docker compose … exec -T waitlist python -m waitlist backup
```

Writes `/data/backups/waitlist-<UTC stamp>.sqlite3` (0600) via SQLite's online
backup API and keeps the newest 14. Run it daily from root's crontab, e.g.
`17 3 * * * cd /opt/swarm-mainnet && docker compose --project-directory /opt/swarm-mainnet --env-file .env -f docker-compose.yml exec -T waitlist python -m waitlist backup >/dev/null 2>&1`.
The privacy page says backups keep a removed entry for up to 14 days: keep 14
copies with a daily run (or fewer).

Export for the operator (CSV with `news_consent`, 0600, newest 5 kept):
`sudo docker compose … exec -T waitlist python -m waitlist export`. It is
personal data: copy it off the volume only where the owner says.

**Purge after the opening.** The privacy page promises that entries without
news consent are deleted within 14 days after public mining has opened on
1 November 2026. Between 1 and 14 November 2026:

```sh
sudo docker compose … exec -T waitlist python -m waitlist purge --without-news-consent --before 2026-11-15          # dry run: prints the count
sudo docker compose … exec -T waitlist python -m waitlist purge --without-news-consent --before 2026-11-15 --yes    # deletes
```

Deletion uses `secure_delete`; the 14 daily backups age out within 14 days.

## 8. Roll back

- Site: redeploy the previous production build. Without the function or the
  Vercel variable the page shows dashes and "could not be reached" messages.
- Caddy: remove the `handle /waitlist/api/*` block, validate, reload.
- Service: `sudo docker compose … stop waitlist && sudo docker compose … rm -f waitlist`.
  The volume `swarm-mainnet-waitlist` keeps the data; delete it only on the
  owner's explicit go (`docker volume rm swarm-mainnet-waitlist`).
- Restore a backup: stop the service, copy a `backups/waitlist-*.sqlite3` over
  `/data/waitlist.sqlite3` (delete `waitlist.sqlite3-wal` / `-shm`), start.
- Secret leaked: generate a new one, set it in both places, restart the
  service, redeploy the site.

## Local development

```sh
cd server/waitlist
python -m unittest discover -s tests                     # unit + integration
WAITLIST_MODE=development WAITLIST_PROXY_SECRET=local-dev-secret \
  WAITLIST_DATA_DIR=./.data WAITLIST_HOST=127.0.0.1 WAITLIST_PORT=18080 \
  WAITLIST_ALLOWED_ORIGINS=http://localhost:4173 WAITLIST_PUBLIC_BASE_URL=http://localhost:4173 \
  python -m waitlist serve
# in the site root, same secret: the preview runs the real function file
WAITLIST_PROXY_SECRET=local-dev-secret node tools/preview.mjs 4173 --waitlist=http://127.0.0.1:18080
```
