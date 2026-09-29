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

Create a D1 database, replace the placeholder `database_id` in `wrangler.jsonc`,
then apply the schema locally or remotely:

```sh
uv run pywrangler d1 migrations apply sdsu-bioinformatics-members --local
uv run pywrangler d1 migrations apply sdsu-bioinformatics-members --remote
```

To load the initial member directory after applying the schema:

```sh
uv run pywrangler d1 migrations apply sdsu-bioinformatics-members --local
```

The current member data in `members.csv` and `members.json` is migration input
only. Production reads should come from D1.
