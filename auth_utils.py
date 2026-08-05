from functools import wraps

from flask import flash, jsonify, redirect, session, url_for

from models import User


def login_required():
    return "user_id" not in session


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)


def login_user(user):
    session["user_id"] = user.id
    session["user"] = user.username
    session["is_admin"] = user.is_admin


def logout_user():
    session.clear()


def admin_required_web():
    if login_required():
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))
    if not session.get("is_admin"):
        flash("Admin access only.", "danger")
        return redirect(url_for("home"))


def api_login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if login_required():
            return jsonify({"ok": False, "error": "Login required"}), 401
        return f(*args, **kwargs)

    return wrapped


def api_admin_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if login_required():
            return jsonify({"ok": False, "error": "Login required"}), 401
        if not session.get("is_admin"):
            return jsonify({"ok": False, "error": "Admin only"}), 403
        return f(*args, **kwargs)

    return wrapped
