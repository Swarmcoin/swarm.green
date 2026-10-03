# Waiting list service: deployment (written, not executed)

The waiting list for public mining (`/waitlist` on swarm.green) talks to this
service. It is Python 3.12 standard library only (no packages), one process,
SQLite in WAL mode in the `/data` volume. Nothing here has been run on a
server; every step needs the owner's go and is the planner's to execute.

Request path in production:

```
browser ── https://swarm.green/api/waitlist/X
   └─ Vercel rewrite (vercel.json) ── https://lwd-main.swarm.green/waitlist/api/X
        └─ Messenger edge Caddy (TLS, 443) ── main-web Caddy (http :8080, site lwd-main)
             └─ handle /waitlist/api/*  ── reverse_proxy waitlist:8080
```

## Endpoints

All under `/waitlist/api/`, JSON in and out, no CORS headers.

| Method | Path | What |
| --- | --- | --- |
| POST | `join` | `{email, address, invite?, consent: true, website: ""}` → `{created, position, total, invites, inviteCode, inviteUrl, invite, confirmed, mail, inviteRule, key?}`; `key` only on the first join |
| GET | `stats` | `{total, updatedUtc}`, `Cache-Control: public, max-age=30` |
| GET | `leaderboard` | top 50 `{rank, label, invites, joinedUtc}`, label = first 8 + `…` + last 4 of the address; 30 s |
| GET / POST | `me` | `?key=` or `{key}` → own position, invites, invite link (the page uses POST so the key never sits in a URL or access log) |
| POST | `delete` | `{key}` → removes the entry and its personal data |
| GET / POST | `confirm` | `?token=` or `{token}`; only when `MAIL_MODE=smtp` |
| GET | `healthz` | `{ok, mail, you, forwardedHeaderUsed, forwardedEntries, publicEntries}` (`you` = first 8 hex of the caller's own salted IP hash; no address is ever shown) |

## Settings (environment)

| Variable | Default | Meaning |
| --- | --- | --- |
| `WAITLIST_DATA_DIR` | `/data` | database `waitlist.sqlite3`, `ip-salt`, `backups/`, `exports/` |
| `WAITLIST_PORT` | `8080` | |
| `WAITLIST_PUBLIC_BASE_URL` | `https://swarm.green` | invite links and mail links |
| `WAITLIST_ALLOWED_ORIGINS` | `https://swarm.green` | a POST with any other `Origin` header gets 403 (no `Origin` is allowed, e.g. curl) |
| `WAITLIST_TRUSTED_PROXIES` | `private_ranges` | comma list of CIDRs; `private_ranges` = 127/8, 10/8, 172.16/12, 192.168/16, 169.254/16, 100.64/10, ::1, fc00::/7, fe80::/10. `X-Forwarded-For` is read only when the direct peer is in this list |
| `WAITLIST_CLIENT_IP` | `leftmost-public` | `leftmost-public`: the left-most valid public address in `X-Forwarded-For`; `rightmost-untrusted`: walk from the right, first address not in the trusted list; `peer`: ignore the header |
| `WAITLIST_IP_SALT` | generated | secret for the IP hash; if unset, 32 random bytes are generated at first start and kept in `/data/ip-salt` (0600). Set it in the env file so it survives a lost volume |
| `WAITLIST_JOIN_PER_IP_PER_HOUR` | `5` | joins (including failed ones) per IP hash |
| `WAITLIST_JOIN_PER_IP_PER_DAY` | `20` | |
| `WAITLIST_JOIN_GLOBAL_PER_MINUTE` | `60` | all joins together |
| `WAITLIST_REQUESTS_PER_IP_PER_MINUTE` | `120` | every endpoint except healthz |
| `MAIL_MODE` | `off` | `off` sends nothing; `smtp` sends one confirmation mail per new entry |
| `SMTP_HOST`, `SMTP_PORT` (587), `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_STARTTLS` (true), `SMTP_SSL` (false), `MAIL_FROM` | | smtp mode only; never logged |

Limits are in memory (a restart resets them). The body limit is 4096 bytes.
IPv6 addresses are hashed by their /64.

**The client address, honestly.** Vercel sends the visitor's address in
`X-Forwarded-For`. Whether it reaches this container depends on the Messenger
edge Caddy: a Caddy that does not trust its peer (Vercel) *replaces* the header
with the peer's address, and then every visitor looks like a Vercel egress
address (per-IP limits become shared, and the "same connection as the inviter"
rule misfires). See step 6. And because `lwd-main.swarm.green` can be reached
without Vercel, a caller can write its own `X-Forwarded-For`: per-IP limits are
a speed bump, the global limit is the wall.

## 1. Copy the folder (on the PC)

`server/waitlist/` of the site repository (commit named in the vault) to
`/opt/swarm-mainnet/waitlist/` on the server, owned by root, mode 0755/0644.
`tests/` may come along; `.dockerignore` keeps it out of the image.

## 2. Build the image (server)

```sh
cd /opt/swarm-mainnet/waitlist
sudo docker pull python:3.12-slim
sudo docker image inspect python:3.12-slim -f '{{index .RepoDigests 0}}'   # note the digest
# optional but recommended: FROM python:3.12-slim@sha256:<that digest> in the Dockerfile
sudo docker build -t swarm-waitlist:0.1.0 .
sudo docker run --rm --read-only -e WAITLIST_DATA_DIR=/tmp/t --tmpfs /tmp swarm-waitlist:0.1.0 \
  python -c "import waitlist.addresses as a; print(a.validate('s1bbQ5zUoR3ttqKiNDVXGhy3NgoQWpWC7GL'))"
```

Go: the last line prints `('s1bbQ5zUoR3ttqKiNDVXGhy3NgoQWpWC7GL', 'p2pkh')`.

## 3. Env file (server)

```sh
sudo install -m 0600 -o root -g root /dev/null /opt/swarm-mainnet/waitlist.env
sudo sh -c 'printf "WAITLIST_IP_SALT=%s\n" "$(openssl rand -hex 32)" >> /opt/swarm-mainnet/waitlist.env'
sudo sh -c 'cat >> /opt/swarm-mainnet/waitlist.env' <<'EOF'
WAITLIST_PUBLIC_BASE_URL=https://swarm.green
WAITLIST_ALLOWED_ORIGINS=https://swarm.green
WAITLIST_TRUSTED_PROXIES=private_ranges
WAITLIST_CLIENT_IP=leftmost-public
MAIL_MODE=off
EOF
```

Never print the file to the screen or a log (it holds the salt).

## 4. Compose service (`/opt/swarm-mainnet/docker-compose.yml`)

Under `services:`:

```yaml
  waitlist:
    image: swarm-waitlist:0.1.0
    restart: unless-stopped
    env_file: ./waitlist.env
    networks: [default]          # default only; main-web reaches it as waitlist:8080
    # no ports: — nothing is published on the host
    volumes:
      - waitlist:/data
    read_only: true
    tmpfs: [/tmp]
    cap_drop: [ALL]
    security_opt: ["no-new-privileges:true"]
    mem_limit: 128m
    cpus: 0.25
    pids_limit: 64
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

Start only this service: `sudo docker compose … up -d waitlist`, then
`sudo docker compose … ps waitlist` → `healthy` within a minute.

## 5. Caddy (`/opt/swarm-mainnet/config/Caddyfile.main-web`)

Inside the `http://{$SWARM_MAIN_LWD_DOMAIN}:8080` site, **before** the gRPC
catch-all handle (the `(swarm_lightwallet)` import), add:

```caddy
	handle /waitlist/api/* {
		request_body {
			max_size 8KB
		}
		reverse_proxy waitlist:8080
	}
```

(`handle` does not strip the prefix; the service expects `/waitlist/api/…`.
Keep any existing site-level `request_body` as it is.) The global
`servers :8080 { trusted_proxies static private_ranges }` already present makes
main-web append, not replace, `X-Forwarded-For` coming from the edge Caddy.

Validate, then reload:

```sh
sudo docker run --rm -v /opt/swarm-mainnet/config/Caddyfile.main-web:/etc/caddy/Caddyfile:ro \
  -e SWARM_MAIN_LWD_DOMAIN=lwd-main.swarm.green -e SWARM_ZAINO_GRPC_PORT=9068 \
  -e SWARM_EXPLORER_PORT=4000 -e SWARM_HSTS_MAX_AGE=31536000 \
  caddy:2.11-alpine caddy validate --config /etc/caddy/Caddyfile
sudo docker compose … exec main-web caddy reload --config /etc/caddy/Caddyfile
```

## 6. CHECK ON HOST: does the visitor's address arrive?

```sh
curl -s https://lwd-main.swarm.green/waitlist/api/healthz   # direct
curl -s https://swarm.green/api/waitlist/healthz              # through Vercel (after the site deploy)
```

Go: through Vercel, `forwardedHeaderUsed: true` and `publicEntries >= 1`; from
two different internet connections (e.g. office and a phone on mobile data) the
`you` values differ, and repeated calls from one connection give the same
`you`. If `you` changes on every call from the same connection, the service is
hashing Vercel's addresses: the Messenger edge Caddy drops Vercel's header.
Fix there (owner's go): in the edge Caddy's `lwd-main.swarm.green` site, for
`/waitlist/api/*` only, `reverse_proxy … { header_up X-Forwarded-For {http.request.header.X-Forwarded-For} }`
or a `trusted_proxies` entry for that site. Do not widen trust for the other sites.

## 7. Test (server, after the site deploy)

```sh
curl -s https://swarm.green/api/waitlist/stats            # {"total":0,...}
curl -s https://swarm.green/api/waitlist/leaderboard      # {"entries":[],...}
```

One end-to-end join with a test address is the owner's call (it puts a real
entry on the public list; remove it afterwards with "Remove me").

## 8. Backups

```sh
sudo docker compose … exec -T waitlist python -m waitlist backup
```

Writes `/data/backups/waitlist-<UTC stamp>.sqlite3` (0600) through SQLite's
online backup API and keeps the newest 14. Run it daily from root's crontab,
e.g. `17 3 * * * cd /opt/swarm-mainnet && docker compose --project-directory /opt/swarm-mainnet --env-file .env -f docker-compose.yml exec -T waitlist python -m waitlist backup >/dev/null 2>&1`.
The privacy page says removed entries leave the backups within 14 days, so keep
the count at 14 with a daily run (or fewer).

Export for the operator (CSV, 0600, in the volume; prints only the path and count):

```sh
sudo docker compose … exec -T waitlist python -m waitlist export
```

Copy it off the volume only to where the owner says; it is personal data.

## 9. Roll back

- Site: redeploy the previous production build (the page falls back to dashes
  and "could not be reached" messages if the API is missing; nothing breaks).
- Caddy: remove the `handle /waitlist/api/*` block, validate, reload.
- Service: `sudo docker compose … stop waitlist && sudo docker compose … rm -f waitlist`.
  The volume `swarm-mainnet-waitlist` keeps the data; delete it only on the
  owner's explicit go (`docker volume rm swarm-mainnet-waitlist`).
- Restore a backup: stop the service, copy a `backups/waitlist-*.sqlite3` over
  `/data/waitlist.sqlite3` (and delete `waitlist.sqlite3-wal` / `-shm`), start.

## Local development

```sh
cd server/waitlist
python -m unittest discover -s tests                     # unit + integration
WAITLIST_DATA_DIR=./.data WAITLIST_HOST=127.0.0.1 WAITLIST_PORT=18080 \
  WAITLIST_ALLOWED_ORIGINS=http://localhost:4173 WAITLIST_PUBLIC_BASE_URL=http://localhost:4173 \
  python -m waitlist serve
# in the site root:
node tools/preview.mjs 4173 --waitlist=http://127.0.0.1:18080
```
