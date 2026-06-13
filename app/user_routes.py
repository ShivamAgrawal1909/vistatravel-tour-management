from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from .decorators import user_login_required
from .extensions import db
from .models import (
    Booking,
    BookingTraveller,
    Enquiry,
    PackageDate,
    Payment,
    Review,
    TourPackage,
    Wishlist,
    add_admin_notification,
)
from .utils import save_upload

user_bp = Blueprint("user", __name__)


@user_bp.route("/")
@user_login_required
def dashboard():
    from .models import User

    user = User.query.get_or_404(session["user_id"])
    bookings = (
        Booking.query.filter_by(user_id=user.id).order_by(Booking.created_at.desc()).limit(10).all()
    )
    stats = {
        "bookings_total": Booking.query.filter_by(user_id=user.id).count(),
        "wishlist": Wishlist.query.filter_by(user_id=user.id).count(),
        "enquiries_open": Enquiry.query.filter_by(user_id=user.id, status="open").count(),
        "pending_payment": Booking.query.filter(
            Booking.user_id == user.id,
            Booking.payment_status == "pending",
            Booking.status != "cancelled",
        ).count(),
    }
    upcoming = (
        Booking.query.filter(
            Booking.user_id == user.id,
            Booking.status.in_(("pending", "confirmed")),
            Booking.package_date_id.isnot(None),
        )
        .join(PackageDate, Booking.package_date_id == PackageDate.id)
        .filter(PackageDate.travel_date >= date.today())
        .order_by(PackageDate.travel_date.asc())
        .first()
    )
    return render_template(
        "user/dashboard.html",
        user=user,
        bookings=bookings,
        stats=stats,
        upcoming=upcoming,
    )


@user_bp.route("/profile", methods=["GET", "POST"])
@user_login_required
def profile():
    from .models import User

    user = User.query.get_or_404(session["user_id"])
    if request.method == "POST":
        user.full_name = request.form.get("full_name", user.full_name).strip()
        user.mobile = request.form.get("mobile", "").strip() or user.mobile
        user.address = request.form.get("address", "").strip() or user.address
        user.gender = request.form.get("gender", "").strip() or user.gender
        f = request.files.get("profile_image")
        path = save_upload(f, "profiles")
        if path:
            user.profile_image = path
        db.session.commit()
        session["user_name"] = user.full_name
        flash("Profile updated.", "success")
        return redirect(url_for("user.profile"))
    return render_template("user/profile.html", user=user)


@user_bp.route("/password", methods=["GET", "POST"])
@user_login_required
def change_password():
    from .models import User

    user = User.query.get_or_404(session["user_id"])
    if request.method == "POST":
        cur = request.form.get("current_password", "")
        p1 = request.form.get("password", "")
        p2 = request.form.get("confirm_password", "")
        if not user.check_password(cur):
            flash("Current password incorrect.", "danger")
        elif p1 != p2 or len(p1) < 6:
            flash("New passwords must match (min 6 chars).", "danger")
        else:
            user.set_password(p1)
            db.session.commit()
            flash("Password changed.", "success")
            return redirect(url_for("user.profile"))
    return render_template("user/change_password.html", user=user)


@user_bp.route("/bookings")
@user_login_required
def bookings():
    from .models import User

    user = User.query.get_or_404(session["user_id"])
    items = Booking.query.filter_by(user_id=user.id).order_by(Booking.created_at.desc()).all()
    return render_template("user/bookings.html", user=user, bookings=items)


@user_bp.route("/bookings/<int:booking_id>/receipt")
@user_login_required
def booking_receipt(booking_id):
    from .models import User

    user = User.query.get_or_404(session["user_id"])
    b = Booking.query.filter_by(id=booking_id, user_id=user.id).first_or_404()
    return render_template("user/booking_receipt.html", booking=b)


@user_bp.route("/bookings/<int:booking_id>")
@user_login_required
def booking_detail(booking_id):
    from .models import User

    user = User.query.get_or_404(session["user_id"])
    b = Booking.query.filter_by(id=booking_id, user_id=user.id).first_or_404()
    payments = b.payments.order_by(Payment.created_at.desc()).all()
    travellers = b.travellers.order_by(BookingTraveller.id).all()
    total_paid = sum(
        float(p.amount or 0) for p in payments if (p.status or "") in ("paid", "partial")
    )
    balance = round(float(b.total_amount or 0) - total_paid, 2)
    return render_template(
        "user/booking_detail.html",
        user=user,
        booking=b,
        payments=payments,
        travellers=travellers,
        total_paid=total_paid,
        balance=balance,
    )


@user_bp.route("/bookings/<int:booking_id>/cancel", methods=["POST"])
@user_login_required
def cancel_booking(booking_id):
    from .models import User

    user = User.query.get_or_404(session["user_id"])
    b = Booking.query.filter_by(id=booking_id, user_id=user.id).first_or_404()
    if b.status in ("cancelled", "completed"):
        flash("Cannot cancel this booking.", "warning")
        return redirect(url_for("user.booking_detail", booking_id=b.id))
    b.status = "cancelled"
    if b.travel_slot:
        b.travel_slot.seats_available += b.travellers_count
    db.session.commit()
    add_admin_notification(
        "booking", f"User cancelled booking {b.public_id}", f"/admin/bookings/{b.id}"
    )
    flash("Cancellation requested / recorded.", "info")
    return redirect(url_for("user.booking_detail", booking_id=b.id))


@user_bp.route("/payments/<int:booking_id>", methods=["GET", "POST"])
@user_login_required
def submit_payment(booking_id):
    from .models import User

    user = User.query.get_or_404(session["user_id"])
    b = Booking.query.filter_by(id=booking_id, user_id=user.id).first_or_404()
    if request.method == "POST":
        amount = request.form.get("amount", type=float)
        mode = request.form.get("mode", "").strip()
        ref = request.form.get("reference_no", "").strip()
        f = request.files.get("proof")
        proof = save_upload(f, "payments")
        if not amount or amount <= 0 or not mode:
            flash("Amount and payment mode required.", "danger")
        else:
            p = Payment(
                booking_id=b.id,
                amount=amount,
                mode=mode,
                reference_no=ref,
                status="pending",
                proof_image=proof,
            )
            db.session.add(p)
            db.session.commit()
            add_admin_notification(
                "payment",
                f"Payment submitted for booking {b.public_id}",
                f"/admin/payments",
            )
            flash("Payment details submitted for verification.", "success")
            return redirect(url_for("user.booking_detail", booking_id=b.id))
    return render_template("user/payment_submit.html", user=user, booking=b)


@user_bp.route("/wishlist")
@user_login_required
def wishlist():
    from .models import User

    user = User.query.get_or_404(session["user_id"])
    items = Wishlist.query.filter_by(user_id=user.id).all()
    return render_template("user/wishlist.html", user=user, items=items)


@user_bp.route("/wishlist/add/<int:pkg_id>", methods=["POST"])
@user_login_required
def wishlist_add(pkg_id):
    user_id = session["user_id"]
    if not Wishlist.query.filter_by(user_id=user_id, package_id=pkg_id).first():
        db.session.add(Wishlist(user_id=user_id, package_id=pkg_id))
        db.session.commit()
        flash("Added to wishlist.", "success")
    return redirect(request.referrer or url_for("public.package_detail", pkg_id=pkg_id))


@user_bp.route("/wishlist/remove/<int:wid>", methods=["POST"])
@user_login_required
def wishlist_remove(wid):
    user_id = session["user_id"]
    w = Wishlist.query.filter_by(id=wid, user_id=user_id).first_or_404()
    pkg_id = w.package_id
    db.session.delete(w)
    db.session.commit()
    flash("Removed from wishlist.", "info")
    return redirect(request.referrer or url_for("public.package_detail", pkg_id=pkg_id))


@user_bp.route("/reviews/<int:pkg_id>", methods=["GET", "POST"])
@user_login_required
def review_package(pkg_id):
    from .models import User

    user = User.query.get_or_404(session["user_id"])
    pkg = TourPackage.query.get_or_404(pkg_id)
    has_booking = Booking.query.filter(
        Booking.user_id == user.id,
        Booking.package_id == pkg.id,
        Booking.status.in_(["confirmed", "completed"]),
    ).first()
    existing = Review.query.filter_by(user_id=user.id, package_id=pkg.id).first()
    if request.method == "POST":
        if not has_booking:
            flash("You can review after a confirmed/completed booking.", "warning")
        else:
            rating = request.form.get("rating", type=int) or 5
            comment = request.form.get("comment", "").strip()
            if existing:
                existing.rating = max(1, min(5, rating))
                existing.comment = comment
                existing.is_approved = False
            else:
                db.session.add(
                    Review(
                        user_id=user.id,
                        package_id=pkg.id,
                        rating=max(1, min(5, rating)),
                        comment=comment,
                        is_approved=False,
                    )
                )
            db.session.commit()
            flash("Review saved (pending admin approval).", "success")
            return redirect(url_for("public.package_detail", pkg_id=pkg.id))
    return render_template(
        "user/review.html",
        user=user,
        package=pkg,
        existing=existing,
        can_review=bool(has_booking),
    )


@user_bp.route("/reviews/delete/<int:rid>", methods=["POST"])
@user_login_required
def review_delete(rid):
    user_id = session["user_id"]
    r = Review.query.filter_by(id=rid, user_id=user_id).first_or_404()
    pkg_id = r.package_id
    db.session.delete(r)
    db.session.commit()
    flash("Review removed.", "info")
    return redirect(url_for("public.package_detail", pkg_id=pkg_id))


@user_bp.route("/enquiries")
@user_login_required
def enquiries():
    from .models import User

    user = User.query.get_or_404(session["user_id"])
    items = Enquiry.query.filter_by(user_id=user.id).order_by(Enquiry.created_at.desc()).all()
    return render_template("user/enquiries.html", user=user, enquiries=items)
