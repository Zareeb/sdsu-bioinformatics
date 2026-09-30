# SDSU Bioinformatics Student Association Website

Website and member administration system for the SDSU Bioinformatics Student
Association (BiSA).

**Website:** https://sdsubioinformatics.org

## Stack

- Python / Flask
- Cloudflare Workers
- Cloudflare D1
- Google OAuth
- `uv` / `pywrangler`
- Squarespace (domain registration only)

## Local development

Requirements:

- Python 3.13+
- `uv`
- Node.js/npm

Install dependencies:

```sh
uv sync
```

Create local environment variables:

```sh
cp .dev.vars.example .dev.vars
```

Then run:

```sh
uv run pywrangler d1 migrations apply bisa-db --local
uv run pywrangler dev --port 8787
```

Open:

```text
http://localhost:8787
```

Local D1 data is separate from production.

## Deployment

Deploy with:

```sh
uv run pywrangler deploy
```

The repository is also connected to Cloudflare for automatic deployments.

Production D1 is `bisa-db`, bound to the Worker as `DB`.

## Admin login

Administrators sign in with Google at:

```text
https://sdsubioinformatics.org/admin
```

The Worker uses:

```text
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET
GOOGLE_ADMIN_EMAILS
SESSION_SECRET
```

`GOOGLE_CLIENT_SECRET` and `SESSION_SECRET` are Cloudflare **secrets**.

`GOOGLE_CLIENT_ID` and `GOOGLE_ADMIN_EMAILS` may be Cloudflare **text variables**.

`GOOGLE_ADMIN_EMAILS` is a comma-separated allowlist:

```text
club@example.com,president@example.com,vp-membership@example.com
```

Do not put OAuth secrets or session secrets in Git.

## Google OAuth

The Google OAuth client needs these authorized redirect URIs:

```text
http://localhost:8787/auth/google/callback
https://sdsubioinformatics.org/auth/google/callback
```

If using the `workers.dev` address for admin login, its callback URI must also
be registered with Google.

## Officer handoff

Before officers leave, make sure incoming officers have the access they need.

At least two current officers should be able to recover or access:

- Cloudflare
- GitHub
- Google Cloud OAuth configuration
- Squarespace domain registration
- Club Gmail

The club Gmail should remain in `GOOGLE_ADMIN_EMAILS` as a permanent recovery
administrator.

When the President or VP of Membership changes:

1. Open Cloudflare → `sdsu-bioinformatics` → Settings → Variables and Secrets.
2. Edit the `GOOGLE_ADMIN_EMAILS` text variable.
3. Add the incoming officer's Google email.
4. Test that the incoming officer can log into `/admin`.
5. Remove outgoing officers who no longer need access.

Do not remove the club Gmail account from the admin list.

## Domain

`sdsubioinformatics.org` is:

- registered through Squarespace
- using Cloudflare DNS
- connected to the `sdsu-bioinformatics` Worker

Do not cancel the Squarespace domain registration just because the website
itself runs on Cloudflare.

## Member data

Production member data lives in D1.

Routine membership changes should be made through `/admin`, not by editing SQL. 🙄

Member exports such as these should not be committed:

```text
members.csv
members.json
members.sql
```

Schema changes belong in `migrations/`.

## D1 migrations

Test migrations locally first:

```sh
uv run pywrangler d1 migrations apply bisa-db --local
```

Apply reviewed migrations to production with:

```sh
uv run pywrangler d1 migrations apply bisa-db --remote
```

The `--remote` command modifies the production database. Don't freestyle SQL
against production unless you have a good reason and preferably a backup. 😩

Member create, update, single delete, and bulk delete operations are recorded in
`member_audit_log`. The admin-only `/admin/audit-log` page displays the newest
200 entries with actor email, operation, member row ID, timestamp, and before /
after snapshots. These snapshots include private member fields; keep access to
the Cloudflare database and admin account restricted to current officers.

## Useful commands

```sh
# Run locally
uv run pywrangler dev --port 8787

# Deploy
uv run pywrangler deploy

# Check Cloudflare login
uv run pywrangler whoami

# Apply local migrations
uv run pywrangler d1 migrations apply bisa-db --local

# Apply production migrations
uv run pywrangler d1 migrations apply bisa-db --remote
```

## Future maintainers

Routine member management requires only `/admin`. You do not need VS Code,
GitHub, Wrangler, or direct database access just to add or edit members.

Keep the architecture simple. This is a student organization website, not a
bank, Kubernetes cluster, or orbital control system.