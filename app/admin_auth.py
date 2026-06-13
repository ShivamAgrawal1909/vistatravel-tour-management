from datetime import datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from .decorators import admin_required
from .extensions import db
from .models import Admin
from .utils import generate_recovery_token, save_upload

admin_auth_bp = Blueprint("admin_auth", __name__)


@admin_auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin_id"):
        return redirect(url_for("admin.dashboard"))
    next_url = request.args.get("next") or request.form.get("next")
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        a = Admin.query.filter(
            (Admin.username == username) | (Admin.email == username)
        ).first()
        if not a or not a.check_password(password):
            flash("Invalid admin credentials.", "danger")
        else:
            session["admin_id"] = a.id
            session["admin_name"] = a.full_name or a.username
            flash("Signed in to admin panel.", "success")
            return redirect(next_url or url_for("admin.dashboard"))
    return render_template("admin/login.html", next_url=next_url)


@admin_auth_bp.route("/logout")
def logout():
    session.pop("admin_id", None)
    session.pop("admin_name", None)
    flash("Admin signed out.", "info")
    return redirect(url_for("admin_auth.login"))


@admin_auth_bp.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        a = Admin.query.filter_by(email=email).first()
        if a:
            a.recovery_token = generate_recovery_token()
            a.recovery_token_expires = datetime.utcnow() + timedelta(hours=24)
            db.session.commit()
            link = url_for("admin_auth.reset", token=a.recovery_token, _external=True)
            flash("Recovery link (demo, no email): " + link, "info")
        else:
            flash("If the email exists, a link would be sent.", "info")
        return redirect(url_for("admin_auth.login"))
    return render_template("admin/forgot.html")


@admin_auth_bp.route("/reset/<token>", methods=["GET", "POST"])
def reset(token):
    a = Admin.query.filter_by(recovery_token=token).first()
    if (
        not a
        or not a.recovery_token_expires
        or a.recovery_token_expires < datetime.utcnow()
    ):
        flash("Invalid or expired link.", "danger")
        return redirect(url_for("admin_auth.forgot"))
    if request.method == "POST":
        p1 = request.form.get("password", "")
        p2 = request.form.get("confirm_password", "")
        if p1 != p2 or len(p1) < 6:
            flash("Passwords must match (min 6 chars).", "danger")
        else:
            a.set_password(p1)
            a.recovery_token = None
            a.recovery_token_expires = None
            db.session.commit()
            flash("Password updated.", "success")
            return redirect(url_for("admin_auth.login"))
    return render_template("admin/reset.html", token=token)


@admin_auth_bp.route("/profile", methods=["GET", "POST"])
@admin_required
def profile():
    a = Admin.query.get_or_404(session["admin_id"])
    if request.method == "POST":
        a.full_name = request.form.get("full_name", a.full_name).strip()
        a.email = request.form.get("email", a.email).strip()
        f = request.files.get("profile_image")
        path = save_upload(f, "admin")
        if path:
            a.profile_image = path
        db.session.commit()
        session["admin_name"] = a.full_name or a.username
        flash("Profile updated.", "success")
        return redirect(url_for("admin_auth.profile"))
    return render_template("admin/profile.html", admin=a)


@admin_auth_bp.route("/password", methods=["GET", "POST"])
@admin_required
def change_password():
    a = Admin.query.get_or_404(session["admin_id"])
    if request.method == "POST":
        cur = request.form.get("current_password", "")
        p1 = request.form.get("password", "")
        p2 = request.form.get("confirm_password", "")
        if not a.check_password(cur):
            flash("Current password incorrect.", "danger")
        elif p1 != p2 or len(p1) < 6:
            flash("New passwords must match.", "danger")
        else:
            a.set_password(p1)
            db.session.commit()
            flash("Password changed.", "success")
            return redirect(url_for("admin_auth.profile"))
    return render_template("admin/change_password.html", admin=a)
