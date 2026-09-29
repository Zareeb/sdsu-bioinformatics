import csv
import hmac
import io
import json
import secrets
from datetime import datetime, timezone
from urllib.parse import urlencode

import httpx
from flask import Flask, abort, redirect, render_template, request, url_for
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from pyodide.ffi import run_sync
from workers import wsgi


app = Flask(
    __name__,
    static_folder="../../static",
    static_url_path="",
)

GOOGLE_AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
SESSION_COOKIE = "sdsu_admin"
STATE_COOKIE = "sdsu_oauth_state"
CSRF_COOKIE = "sdsu_admin_csrf"
SESSION_MAX_AGE = 60 * 60 * 8
STATE_MAX_AGE = 60 * 10


def _database():
    return getattr(request.environ.get("workers.env"), "DB", None)


def _environment():
    return request.environ.get("workers.env")


def _setting(name):
    return getattr(_environment(), name, None)


def _serializer(salt):
    secret = _setting("SESSION_SECRET")
    if not secret:
        abort(503, description="SESSION_SECRET is not configured")
    return URLSafeTimedSerializer(secret, salt=salt)


def _admin_emails():
    raw_emails = _setting("GOOGLE_ADMIN_EMAILS") or ""
    return {
        email.strip().lower()
        for email in raw_emails.split(",")
        if email.strip()
    }


def _oauth_ready():
    required = ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_ADMIN_EMAILS")
    return all(_setting(name) for name in required) and bool(_admin_emails())


def _session_user():
    value = request.cookies.get(SESSION_COOKIE)
    if not value:
        return None
    try:
        return _serializer("admin-session").loads(value, max_age=SESSION_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None


def _require_admin():
    user = _session_user()
    if user is None:
        return redirect(url_for("google_login", next=request.path))
    email = user.get("email") if isinstance(user, dict) else None
    if not isinstance(email, str) or email.strip().lower() not in _admin_emails():
        response = app.response_class(
            "I'm sorry Dave, I'm afraid I can't do that.",
            status=403,
            mimetype="text/plain",
        )
        for cookie in (SESSION_COOKIE, CSRF_COOKIE, STATE_COOKIE):
            response.delete_cookie(
                cookie,
                path="/",
                secure=True,
                httponly=True,
                samesite="Lax",
            )
        return response
    return user


def _csrf_token():
    return secrets.token_urlsafe(32)


def _check_csrf():
    submitted = request.form.get("csrf_token", "")
    cookie = request.cookies.get(CSRF_COOKIE, "")
    if not submitted or not cookie or not hmac.compare_digest(submitted, cookie):
        abort(400, description="Invalid CSRF token")


def _member_values():
    values = {
        "first_name": request.form.get("first_name", "").strip(),
        "last_name": request.form.get("last_name", "").strip(),
        "major": request.form.get("major", "").strip(),
        "status": request.form.get("status", "").strip(),
        "email": request.form.get("email", "").strip().lower(),
        "position": request.form.get("position", "").strip(),
        "public": 1 if request.form.get("public") == "1" else 0,
    }
    limits = {
        "first_name": 80,
        "last_name": 120,
        "major": 160,
        "status": 80,
        "email": 254,
        "position": 120,
    }
    if any(not values[field] for field in ("first_name", "last_name", "major")):
        abort(400, description="First name, last name, and major are required")
    if any(len(values[field]) > limit for field, limit in limits.items()):
        abort(400, description="One or more member fields are too long")
    return values


def _admin_members():
    database = _database()
    if database is None:
        abort(503, description="D1 database is not configured")
    result = run_sync(
        database.prepare(
            """
                 SELECT rowid AS id, first_name, last_name, major, status, email,
                     position, public, created_at, updated_at
            FROM members
            ORDER BY last_name, first_name
            """
        ).all()
    )
    return result.results


@app.get("/")
def home():
    return render_template("home.html")


@app.get("/members")
@app.get("/members/")
def members():
    database = _database()
    if database is None:
        return render_template("members.html", members=[], database_configured=False)

    result = run_sync(
        database.prepare(
            """
            SELECT rowid AS id, first_name, last_name, major, status, position, public
            FROM members
            WHERE public = 1
            ORDER BY last_name, first_name
            """
        ).all()
    )
    return render_template(
        "members.html",
        members=result.results,
        database_configured=True,
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/auth/google")
def google_login():
    if not _oauth_ready():
        abort(503, description="Google OAuth is not configured")

    next_url = request.args.get("next", "/admin")
    if not next_url.startswith("/") or next_url.startswith("//"):
        next_url = "/admin"

    state = _serializer("oauth-state").dumps({"next": next_url})
    callback_url = url_for("google_callback", _external=True)
    params = {
        "client_id": _setting("GOOGLE_CLIENT_ID"),
        "redirect_uri": callback_url,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    response = redirect(f"{GOOGLE_AUTHORIZATION_URL}?{urlencode(params)}")
    response.set_cookie(
        STATE_COOKIE,
        state,
        max_age=STATE_MAX_AGE,
        httponly=True,
        secure=True,
        samesite="Lax",
    )
    return response


@app.get("/auth/google/callback")
def google_callback():
    if not _oauth_ready():
        abort(503, description="Google OAuth is not configured")
    if request.args.get("error"):
        abort(401, description="Google OAuth was not completed")

    state = request.args.get("state", "")
    if not state or state != request.cookies.get(STATE_COOKIE):
        abort(400, description="Invalid OAuth state")
    try:
        state_data = _serializer("oauth-state").loads(state, max_age=STATE_MAX_AGE)
    except (BadSignature, SignatureExpired):
        abort(400, description="Expired OAuth state")

    code = request.args.get("code")
    if not code:
        abort(400, description="Missing OAuth authorization code")

    callback_url = url_for("google_callback", _external=True)
    with httpx.Client(timeout=10.0) as client:
        token_response = client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": _setting("GOOGLE_CLIENT_ID"),
                "client_secret": _setting("GOOGLE_CLIENT_SECRET"),
                "redirect_uri": callback_url,
                "grant_type": "authorization_code",
            },
        )
        if token_response.status_code != 200:
            abort(401, description="Google token exchange failed")

        access_token = token_response.json().get("access_token")
        if not access_token:
            abort(401, description="Google token response had no access token")

        user_response = client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_response.status_code != 200:
            abort(401, description="Google user lookup failed")
        profile = user_response.json()

    email = str(profile.get("email", "")).strip().lower()
    if not email or not profile.get("email_verified") or email not in _admin_emails():
        abort(403, description="Google account is not an approved administrator")

    session = _serializer("admin-session").dumps(
        {
            "email": email,
            "name": profile.get("name", email),
            "sub": profile.get("sub", ""),
        }
    )
    response = redirect(state_data.get("next", "/admin"))
    response.set_cookie(
        SESSION_COOKIE,
        session,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=True,
        samesite="Lax",
    )
    response.delete_cookie(STATE_COOKIE)
    return response


@app.get("/auth/logout")
def logout():
    response = redirect(url_for("home"))
    response.delete_cookie(SESSION_COOKIE)
    response.delete_cookie(STATE_COOKIE)
    return response


@app.get("/admin")
def admin():
    user = _require_admin()
    if not isinstance(user, dict):
        return user
    csrf_token = _csrf_token()
    response = render_template(
        "admin.html",
        user=user,
        members=_admin_members(),
        csrf_token=csrf_token,
    )
    response = app.make_response(response)
    response.set_cookie(
        CSRF_COOKIE,
        csrf_token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=True,
        samesite="Lax",
    )
    return response


@app.get("/admin/export/backup.json")
def export_backup():
    user = _require_admin()
    if not isinstance(user, dict):
        return user
    payload = {
        "format_version": 1,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "members": [dict(member) for member in _admin_members()],
    }
    response = app.response_class(
        json.dumps(payload, indent=2),
        mimetype="application/json",
    )
    response.headers["Content-Disposition"] = 'attachment; filename="members-backup.json"'
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/admin/export/members.csv")
def export_members_csv():
    user = _require_admin()
    if not isinstance(user, dict):
        return user

    fields = (
        "id",
        "first_name",
        "last_name",
        "major",
        "status",
        "email",
        "position",
        "public",
        "created_at",
        "updated_at",
    )
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for member in _admin_members():
        row = {}
        for field in fields:
            value = member.get(field)
            text = "" if value is None else str(value)
            if text.lstrip(" \t\r\n").startswith(("=", "+", "-", "@")):
                text = "'" + text
            row[field] = text
        writer.writerow(row)

    response = app.response_class(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = 'attachment; filename="members.csv"'
    response.headers["Cache-Control"] = "no-store"
    return response


@app.post("/admin/members")
def create_member():
    user = _require_admin()
    if not isinstance(user, dict):
        return user
    _check_csrf()
    values = _member_values()
    database = _database()
    if database is None:
        abort(503, description="D1 database is not configured")
    run_sync(
        database.prepare(
            """
            INSERT INTO members (first_name, last_name, major, status, email, position, public)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
        )
        .bind(
            values["first_name"],
            values["last_name"],
            values["major"],
            values["status"],
            values["email"],
            values["position"],
            values["public"],
        )
        .run()
    )
    return redirect(url_for("admin"))


@app.post("/admin/members/<int:member_id>/update")
def update_member(member_id):
    user = _require_admin()
    if not isinstance(user, dict):
        return user
    _check_csrf()
    values = _member_values()
    database = _database()
    if database is None:
        abort(503, description="D1 database is not configured")
    result = run_sync(
        database.prepare(
            """
            UPDATE members
            SET first_name = ?, last_name = ?, major = ?, status = ?, email = ?,
                position = ?, public = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE rowid = ?
            """
        )
        .bind(
            values["first_name"],
            values["last_name"],
            values["major"],
            values["status"],
            values["email"],
            values["position"],
            values["public"],
            member_id,
        )
        .run()
    )
    if result.meta.rows_written == 0:
        abort(404, description="Member not found")
    return redirect(url_for("admin"))


@app.post("/admin/members/<int:member_id>/delete")
def delete_member(member_id):
    user = _require_admin()
    if not isinstance(user, dict):
        return user
    _check_csrf()
    database = _database()
    if database is None:
        abort(503, description="D1 database is not configured")
    result = run_sync(
        database.prepare("DELETE FROM members WHERE rowid = ?").bind(member_id).run()
    )
    if result.meta.rows_written == 0:
        abort(404, description="Member not found")
    return redirect(url_for("admin"))


Default = wsgi.entrypoint(app)