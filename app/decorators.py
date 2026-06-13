from functools import wraps

from flask import flash, redirect, request, session, url_for


def user_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("auth.user_login", next=request.path))
        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_id"):
            flash("Admin login required.", "warning")
            return redirect(url_for("admin_auth.login", next=request.path))
        return f(*args, **kwargs)

    return decorated
