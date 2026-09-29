## Development

This site runs as a Python Worker using Flask, Jinja, and Cloudflare D1.
The Worker application entrypoint is `src/sdsu_bioinformatics/app.py`.

Install dependencies and start the local Worker:

```sh
uv sync
uv run pywrangler dev
```

For local Google OAuth configuration, copy `.dev.vars.example` to `.dev.vars`
and replace every placeholder. Register this callback URL in Google Cloud:

```text
http://localhost:8787/auth/google/callback
```

For deployment, configure the same values as Worker secrets or environment
bindings. `GOOGLE_ADMIN_EMAILS` is a comma-separated explicit allowlist; an
authenticated Google account not in that list is rejected.

The D1 database binding is configured in `wrangler.jsonc`. Apply pending schema
migrations to the local or remote database with:

```sh
uv run pywrangler d1 migrations apply bisa-db --local
uv run pywrangler d1 migrations apply bisa-db --remote
```

`migrations/0001_create_members.sql` defines the current live schema and does
not seed member data. Production D1 already has the older seed and additive
migrations recorded, so use `0004_*.sql` or a higher prefix for future
migrations. New databases can start from the current DDL baseline.

Production member reads and updates use D1. A live export in `members.sql` may
contain private member data and is ignored by Git; do not publish it.
