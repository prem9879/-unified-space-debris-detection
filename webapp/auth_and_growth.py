"""Authentication, legal, billing, and growth routes for the Flask app."""

from __future__ import annotations

import json
import os
import secrets
import sqlite3
import time
from functools import wraps
from pathlib import Path
from typing import Any

from flask import Blueprint, Response, current_app, g, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

bp = Blueprint("auth_and_growth", __name__)


def _db_path() -> Path:
    raw = os.getenv("USDD_AUTH_DB_PATH", "").strip()
    if raw:
        return Path(raw)
    root = Path(str(current_app.config.get("USDD_ROOT", Path.cwd())))
    return root / "artifacts" / "auth_growth.sqlite3"


def _login_lock_threshold() -> int:
    return max(3, int(os.getenv("USDD_LOGIN_LOCK_THRESHOLD", "5")))


def _login_lock_seconds() -> int:
    return max(60, int(os.getenv("USDD_LOGIN_LOCK_SECONDS", "600")))


def _connect() -> sqlite3.Connection:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    _ensure_schema(conn)
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            email_verified INTEGER NOT NULL DEFAULT 0,
            plan TEXT NOT NULL DEFAULT 'free',
            subscription_status TEXT NOT NULL DEFAULT 'inactive',
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS auth_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT NOT NULL UNIQUE,
            token_type TEXT NOT NULL,
            expires_at INTEGER NOT NULL,
            used_at INTEGER,
            created_at INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS auth_failures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            identity TEXT NOT NULL UNIQUE,
            failures INTEGER NOT NULL DEFAULT 0,
            locked_until INTEGER NOT NULL DEFAULT 0,
            updated_at INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS app_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            path TEXT,
            user_id INTEGER,
            metadata_json TEXT
        );
        """
    )
    conn.commit()


def _mailbox_path() -> Path:
    root = Path(str(current_app.config.get("USDD_ROOT", Path.cwd())))
    return root / "logs" / "auth_mailbox.log"


def _record_mail(kind: str, email: str, link: str) -> None:
    mailbox = _mailbox_path()
    mailbox.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "ts": int(time.time()),
        "kind": kind,
        "email": email,
        "link": link,
    }
    with mailbox.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def _record_event(event_type: str, path: str | None, user_id: int | None, metadata: dict[str, Any] | None = None) -> None:
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO app_events(ts, event_type, path, user_id, metadata_json) VALUES (?, ?, ?, ?, ?)",
            (
                int(time.time()),
                event_type,
                path,
                user_id,
                json.dumps(metadata or {}),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _token_for_user(user_id: int, token_type: str, ttl_seconds: int) -> str:
    token = secrets.token_urlsafe(32)
    now = int(time.time())
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO auth_tokens(user_id, token, token_type, expires_at, used_at, created_at) VALUES (?, ?, ?, ?, NULL, ?)",
            (user_id, token, token_type, now + ttl_seconds, now),
        )
        conn.commit()
    finally:
        conn.close()
    return token


def _load_current_user() -> dict[str, Any] | None:
    user_id = session.get("user_id")
    if not user_id:
        return None

    conn = _connect()
    try:
        row = conn.execute(
            "SELECT id, email, email_verified, plan, subscription_status FROM users WHERE id = ?",
            (int(user_id),),
        ).fetchone()
        if not row:
            return None
        return {
            "id": int(row["id"]),
            "email": str(row["email"]),
            "email_verified": bool(row["email_verified"]),
            "plan": str(row["plan"]),
            "subscription_status": str(row["subscription_status"]),
        }
    finally:
        conn.close()


def _login_identity(email: str) -> str:
    ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or (request.remote_addr or "unknown")
    return f"{ip}|{email.strip().lower()}"


def _is_login_locked(identity: str) -> tuple[bool, int]:
    conn = _connect()
    try:
        row = conn.execute("SELECT locked_until FROM auth_failures WHERE identity = ?", (identity,)).fetchone()
        if not row:
            return False, 0
        until = int(row["locked_until"])
        return until > int(time.time()), until
    finally:
        conn.close()


def _register_login_failure(identity: str) -> tuple[int, int]:
    now = int(time.time())
    conn = _connect()
    try:
        row = conn.execute("SELECT failures FROM auth_failures WHERE identity = ?", (identity,)).fetchone()
        failures = int(row["failures"]) + 1 if row else 1
        lock_until = now + _login_lock_seconds() if failures >= _login_lock_threshold() else 0
        if row:
            conn.execute(
                "UPDATE auth_failures SET failures = ?, locked_until = ?, updated_at = ? WHERE identity = ?",
                (failures, lock_until, now, identity),
            )
        else:
            conn.execute(
                "INSERT INTO auth_failures(identity, failures, locked_until, updated_at) VALUES (?, ?, ?, ?)",
                (identity, failures, lock_until, now),
            )
        conn.commit()
        return failures, lock_until
    finally:
        conn.close()


def _clear_login_failures(identity: str) -> None:
    conn = _connect()
    try:
        conn.execute("DELETE FROM auth_failures WHERE identity = ?", (identity,))
        conn.commit()
    finally:
        conn.close()


def _json_or_redirect(message: str, status: int = 200, target: str = "/"):
    wants_json = request.headers.get("Accept", "").lower().find("application/json") >= 0
    if wants_json:
        return jsonify({"message": message}), status
    if status >= 400:
        return render_template("auth_message.html", title="Request Failed", message=message, status=status), status
    return redirect(target)


def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        g.current_user = _load_current_user()
        if not g.current_user:
            return redirect(url_for("auth_and_growth.login", next=request.path))
        return fn(*args, **kwargs)

    return wrapped


@bp.before_app_request
def attach_user_and_track_pages() -> None:
    g.current_user = _load_current_user()
    if request.method != "GET":
        return
    if request.path.startswith("/static") or request.path.startswith("/assets"):
        return
    if request.path.endswith(".css") or request.path.endswith(".js"):
        return
    user_id = int(g.current_user["id"]) if g.current_user else None
    _record_event("page_view", request.path, user_id, {"query": dict(request.args)})


@bp.get("/privacy-policy")
def privacy_policy():
    return render_template("privacy_policy.html")


@bp.get("/terms-of-service")
def terms_of_service():
    return render_template("terms_of_service.html")


@bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm = request.form.get("confirm_password", "")

    if not email or "@" not in email:
        return _json_or_redirect("A valid email address is required.", status=400)
    if len(password) < 8:
        return _json_or_redirect("Password must be at least 8 characters.", status=400)
    if password != confirm:
        return _json_or_redirect("Password confirmation does not match.", status=400)

    now = int(time.time())
    conn = _connect()
    try:
        exists = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if exists:
            return _json_or_redirect("An account with that email already exists.", status=409)

        conn.execute(
            "INSERT INTO users(email, password_hash, email_verified, created_at, updated_at) VALUES (?, ?, 0, ?, ?)",
            (email, generate_password_hash(password), now, now),
        )
        conn.commit()
        user_id = int(conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()["id"])
    finally:
        conn.close()

    token = _token_for_user(user_id, "email_verify", ttl_seconds=24 * 3600)
    verify_link = request.url_root.rstrip("/") + url_for("auth_and_growth.verify_email") + f"?token={token}"
    _record_mail("verify_email", email, verify_link)

    _record_event("signup", "/signup", user_id, {"email": email})
    return render_template(
        "auth_message.html",
        title="Verify Your Email",
        message="Your account was created. A verification link was generated and written to logs/auth_mailbox.log.",
        detail=verify_link,
        status=200,
    )


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    identity = _login_identity(email)

    locked, until = _is_login_locked(identity)
    if locked:
        return _json_or_redirect(f"Too many failed attempts. Try again after {until}.", status=429)

    conn = _connect()
    try:
        row = conn.execute("SELECT id, password_hash, email_verified FROM users WHERE email = ?", (email,)).fetchone()
    finally:
        conn.close()

    if not row or not check_password_hash(str(row["password_hash"]), password):
        failures, lock_until = _register_login_failure(identity)
        msg = "Invalid credentials."
        if lock_until > 0:
            msg = f"Invalid credentials. Account locked temporarily until {lock_until}."
        return _json_or_redirect(msg, status=401)

    if not bool(row["email_verified"]):
        token = _token_for_user(int(row["id"]), "email_verify", ttl_seconds=24 * 3600)
        verify_link = request.url_root.rstrip("/") + url_for("auth_and_growth.verify_email") + f"?token={token}"
        _record_mail("verify_email", email, verify_link)
        return render_template(
            "auth_message.html",
            title="Email Verification Required",
            message="Please verify your email first. A fresh verification link was generated.",
            detail=verify_link,
            status=403,
        ), 403

    _clear_login_failures(identity)
    session["user_id"] = int(row["id"])
    session["user_email"] = email
    _record_event("login_success", "/login", int(row["id"]), {})

    next_path = request.args.get("next") or request.form.get("next") or "/"
    return redirect(next_path)


@bp.post("/logout")
def logout():
    user_id = session.get("user_id")
    if user_id:
        _record_event("logout", "/logout", int(user_id), {})
    session.clear()
    return redirect("/")


@bp.get("/verify-email")
def verify_email():
    token = request.args.get("token", "").strip()
    if not token:
        return _json_or_redirect("Missing verification token.", status=400)

    now = int(time.time())
    conn = _connect()
    try:
        row = conn.execute(
            """
            SELECT id, user_id, expires_at, used_at
            FROM auth_tokens
            WHERE token = ? AND token_type = 'email_verify'
            """,
            (token,),
        ).fetchone()
        if not row:
            return _json_or_redirect("Invalid verification token.", status=404)
        if row["used_at"] is not None:
            return _json_or_redirect("Token already used.", status=409)
        if int(row["expires_at"]) < now:
            return _json_or_redirect("Verification token expired.", status=410)

        conn.execute("UPDATE users SET email_verified = 1, updated_at = ? WHERE id = ?", (now, int(row["user_id"])))
        conn.execute("UPDATE auth_tokens SET used_at = ? WHERE id = ?", (now, int(row["id"])))
        conn.commit()
    finally:
        conn.close()

    return render_template(
        "auth_message.html",
        title="Email Verified",
        message="Your email is now verified. You can sign in.",
        status=200,
    )


@bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "GET":
        return render_template("forgot_password.html")

    email = request.form.get("email", "").strip().lower()
    conn = _connect()
    try:
        row = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    finally:
        conn.close()

    if row:
        token = _token_for_user(int(row["id"]), "password_reset", ttl_seconds=3600)
        reset_link = request.url_root.rstrip("/") + url_for("auth_and_growth.reset_password", token=token)
        _record_mail("password_reset", email, reset_link)
    else:
        reset_link = "If this email exists, a reset link has been generated."

    return render_template(
        "auth_message.html",
        title="Reset Link Generated",
        message="If your account exists, a reset link was generated and written to logs/auth_mailbox.log.",
        detail=reset_link,
        status=200,
    )


@bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token: str):
    now = int(time.time())
    conn = _connect()
    try:
        row = conn.execute(
            """
            SELECT id, user_id, expires_at, used_at
            FROM auth_tokens
            WHERE token = ? AND token_type = 'password_reset'
            """,
            (token,),
        ).fetchone()
        if not row:
            return _json_or_redirect("Invalid password reset token.", status=404)
        if row["used_at"] is not None:
            return _json_or_redirect("Reset token already used.", status=409)
        if int(row["expires_at"]) < now:
            return _json_or_redirect("Reset token expired.", status=410)

        if request.method == "GET":
            return render_template("reset_password.html", token=token)

        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if len(password) < 8:
            return _json_or_redirect("Password must be at least 8 characters.", status=400)
        if password != confirm:
            return _json_or_redirect("Password confirmation does not match.", status=400)

        conn.execute(
            "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?",
            (generate_password_hash(password), now, int(row["user_id"])),
        )
        conn.execute("UPDATE auth_tokens SET used_at = ? WHERE id = ?", (now, int(row["id"])))
        conn.commit()
    finally:
        conn.close()

    return render_template(
        "auth_message.html",
        title="Password Updated",
        message="Your password has been reset. You can now log in.",
        status=200,
    )


@bp.get("/auth/google")
def auth_google_start():
    if os.getenv("USDD_ENABLE_GOOGLE_AUTH", "false").strip().lower() not in {"1", "true", "yes", "on"}:
        return jsonify({"enabled": False, "message": "Google auth is disabled. Set USDD_ENABLE_GOOGLE_AUTH=true and configure OAuth credentials."}), 501
    return jsonify({"enabled": True, "message": "Google OAuth callback integration can be wired with Authlib. Credentials are not configured in this project yet."}), 501


@bp.get("/billing")
@login_required
def billing_home():
    user = g.current_user
    return render_template("billing.html", user=user)


def _set_subscription(user_id: int, plan: str, status: str) -> None:
    now = int(time.time())
    conn = _connect()
    try:
        conn.execute(
            "UPDATE users SET plan = ?, subscription_status = ?, updated_at = ? WHERE id = ?",
            (plan, status, now, user_id),
        )
        conn.commit()
    finally:
        conn.close()


@bp.post("/billing/checkout")
@login_required
def billing_checkout():
    plan = request.form.get("plan", "starter").strip().lower() or "starter"
    outcome = request.form.get("outcome", "success").strip().lower() or "success"
    valid_plans = {"starter", "pro", "enterprise"}
    if plan not in valid_plans:
        return jsonify({"error": "Invalid plan."}), 400

    user = g.current_user
    if outcome == "success":
        _set_subscription(int(user["id"]), plan, "active")
        _record_event("billing_checkout_success", request.path, int(user["id"]), {"plan": plan})
        return jsonify({"status": "success", "plan": plan, "subscription_status": "active"})

    _record_event("billing_checkout_failed", request.path, int(user["id"]), {"plan": plan})
    return jsonify({"status": "failed", "reason": "Card declined in simulated gateway", "plan": plan}), 402


@bp.post("/billing/subscription/upgrade")
@login_required
def subscription_upgrade():
    tiers = ["free", "starter", "pro", "enterprise"]
    user = g.current_user
    current_plan = str(user.get("plan", "free"))
    idx = max(0, tiers.index(current_plan) if current_plan in tiers else 0)
    new_plan = tiers[min(len(tiers) - 1, idx + 1)]
    _set_subscription(int(user["id"]), new_plan, "active")
    _record_event("subscription_upgrade", request.path, int(user["id"]), {"from": current_plan, "to": new_plan})
    return jsonify({"status": "success", "from": current_plan, "to": new_plan})


@bp.post("/billing/subscription/downgrade")
@login_required
def subscription_downgrade():
    tiers = ["free", "starter", "pro", "enterprise"]
    user = g.current_user
    current_plan = str(user.get("plan", "free"))
    idx = max(0, tiers.index(current_plan) if current_plan in tiers else 0)
    new_plan = tiers[max(0, idx - 1)]
    status = "inactive" if new_plan == "free" else "active"
    _set_subscription(int(user["id"]), new_plan, status)
    _record_event("subscription_downgrade", request.path, int(user["id"]), {"from": current_plan, "to": new_plan})
    return jsonify({"status": "success", "from": current_plan, "to": new_plan, "subscription_status": status})


@bp.post("/track_event")
def track_event():
    payload = request.get_json(silent=True) or {}
    event_name = str(payload.get("event", "")).strip() or "custom_event"
    metadata = payload.get("properties", {})
    user_id = int(g.current_user["id"]) if getattr(g, "current_user", None) else None
    _record_event(event_name, request.path, user_id, metadata if isinstance(metadata, dict) else {"raw": metadata})
    return jsonify({"status": "ok", "event": event_name})


@bp.get("/robots.txt")
def robots() -> Response:
    content = """User-agent: *
Allow: /
Sitemap: /sitemap.xml
"""
    return Response(content, mimetype="text/plain")


@bp.get("/sitemap.xml")
def sitemap() -> Response:
    base = request.url_root.rstrip("/")
    urls = [
        "/",
        "/privacy-policy",
        "/terms-of-service",
        "/signup",
        "/login",
        "/billing",
    ]
    rows = "".join([f"<url><loc>{base}{path}</loc></url>" for path in urls])
    payload = f"<?xml version=\"1.0\" encoding=\"UTF-8\"?><urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">{rows}</urlset>"
    return Response(payload, mimetype="application/xml")


def init_auth_and_growth(app, root_path: Path) -> None:
    app.config["USDD_ROOT"] = str(root_path)
    app.register_blueprint(bp)
