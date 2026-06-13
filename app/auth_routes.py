from datetime import datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from .extensions import db
from .models import User
from .utils import generate_recovery_token, save_upload

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("user.dashboard"))
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        mobile = request.form.get("mobile", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        address = request.form.get("address", "").strip()
        gender = request.form.get("gender", "").strip()
        if not full_name or not email or not password:
            flash("Please complete required fields.", "danger")
        elif password != confirm:
            flash("Passwords do not match.", "danger")
        elif User.query.filter_by(email=email).first():
            flash("Email already registered.", "warning")
        else:
            u = User(
                full_name=full_name,
                email=email,
                mobile=mobile,
                address=address or None,
                gender=gender or None,
            )
            u.set_password(password)
            db.session.add(u)
            db.session.commit()
            flash("Account created. Please sign in.", "success")
            return redirect(url_for("auth.user_login"))
    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def user_login():
    if session.get("user_id"):
        return redirect(url_for("user.dashboard"))
    next_url = request.args.get("next") or request.form.get("next")
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        u = User.query.filter_by(email=email).first()
        if not u or not u.is_active or not u.check_password(password):
            flash("Invalid credentials or inactive account.", "danger")
        else:
            session["user_id"] = u.id
            session["user_name"] = u.full_name
            flash("Welcome back.", "success")
            return redirect(next_url or url_for("user.dashboard"))
    return render_template("auth/login.html", next_url=next_url)


@auth_bp.route("/logout")
def user_logout():
    session.pop("user_id", None)
    session.pop("user_name", None)
    flash("Signed out.", "info")
    return redirect(url_for("public.home"))


@auth_bp.route("/forgot", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        u = User.query.filter_by(email=email).first()
        if u:
            u.recovery_token = generate_recovery_token()
            u.recovery_token_expires = datetime.utcnow() + timedelta(hours=24)
            db.session.commit()
            link = url_for("auth.reset_password", token=u.recovery_token, _external=True)
            flash(
                "Recovery link generated (demo — no email API). Use this link: "
                + link,
                "info",
            )
        else:
            flash("If the email exists, instructions would be sent.", "info")
        return redirect(url_for("auth.user_login"))
    return render_template("auth/forgot.html")


@auth_bp.route("/reset/<token>", methods=["GET", "POST"])
def reset_password(token):
    u = User.query.filter_by(recovery_token=token).first()
    if (
        not u
        or not u.recovery_token_expires
        or u.recovery_token_expires < datetime.utcnow()
    ):
        flash("Invalid or expired link.", "danger")
        return redirect(url_for("auth.forgot_password"))
    if request.method == "POST":
        p1 = request.form.get("password", "")
        p2 = request.form.get("confirm_password", "")
        if p1 != p2 or len(p1) < 6:
            flash("Passwords must match and be at least 6 characters.", "danger")
        else:
            u.set_password(p1)
            u.recovery_token = None
            u.recovery_token_expires = None
            db.session.commit()
            flash("Password updated. Please sign in.", "success")
            return redirect(url_for("auth.user_login"))
    return render_template("auth/reset.html", token=token)
