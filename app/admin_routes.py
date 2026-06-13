import csv
import io
import json
from datetime import datetime, timedelta

from flask import (
    Blueprint,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy import func, or_

from .decorators import admin_required
from .extensions import db
from .models import (
    AdminNotification,
    Booking,
    BookingTraveller,
    Brand,
    Category,
    Coupon,
    CouponUsage,
    Destination,
    Enquiry,
    GalleryImage,
    HomepageSetting,
    Hotel,
    Offer,
    PackageDate,
    PackageImage,
    Payment,
    Review,
    Slider,
    StaticPage,
    Testimonial,
    TourPackage,
    Transport,
    User,
    Wishlist,
)
from .utils import save_upload

admin_bp = Blueprint("admin", __name__)


def _notif_counts():
    unread = AdminNotification.query.filter_by(is_read=False).count()
    pending_bookings = Booking.query.filter_by(status="pending").count()
    return unread, pending_bookings


@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    stats = {
        "users": User.query.count(),
        "packages": TourPackage.query.count(),
        "brands": Brand.query.count(),
        "bookings": Booking.query.count(),
        "pending_bookings": Booking.query.filter_by(status="pending").count(),
        "confirmed_bookings": Booking.query.filter_by(status="confirmed").count(),
        "cancelled_bookings": Booking.query.filter_by(status="cancelled").count(),
        "enquiries": Enquiry.query.count(),
    }
    pay = db.session.query(Payment.status, func.count(Payment.id)).group_by(Payment.status).all()
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(10).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    notif_unread, pending_alert = _notif_counts()
    notifications = (
        AdminNotification.query.order_by(AdminNotification.created_at.desc()).limit(15).all()
    )
    return render_template(
        "admin/dashboard.html",
        stats=stats,
        payment_summary=dict(pay),
        recent_bookings=recent_bookings,
        recent_users=recent_users,
        notifications=notifications,
        notif_unread=notif_unread,
        pending_alert=pending_alert,
    )


@admin_bp.route("/notifications/read-all", methods=["POST"])
@admin_required
def notifications_read_all():
    AdminNotification.query.update(
        {AdminNotification.is_read: True}, synchronize_session=False
    )
    db.session.commit()
    flash("Notifications marked read.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/notifications/<int:nid>/read", methods=["POST"])
@admin_required
def notification_mark_read(nid):
    n = AdminNotification.query.get_or_404(nid)
    n.is_read = True
    db.session.commit()
    dest = request.form.get("next") or n.link or url_for("admin.dashboard")
    return redirect(dest)


# --- Brands ---
@admin_bp.route("/brands")
@admin_required
def brands():
    q = Brand.query
    if request.args.get("q"):
        q = q.filter(Brand.name.ilike(f"%{request.args['q']}%"))
    if request.args.get("status") == "active":
        q = q.filter(Brand.is_active == True)
    elif request.args.get("status") == "inactive":
        q = q.filter(Brand.is_active == False)
    items = q.order_by(Brand.name).all()
    return render_template("admin/brands_list.html", items=items)


@admin_bp.route("/brands/new", methods=["GET", "POST"])
@admin_bp.route("/brands/<int:bid>/edit", methods=["GET", "POST"])
@admin_required
def brand_form(bid=None):
    b = Brand.query.get(bid) if bid else None
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        desc = request.form.get("description", "").strip()
        active = request.form.get("is_active") == "on"
        logo = save_upload(request.files.get("logo"), "brands")
        if not name:
            flash("Name required.", "danger")
        else:
            if not b:
                b = Brand(name=name)
            b.name = name
            b.description = desc
            b.is_active = active
            if logo:
                b.logo = logo
            db.session.add(b)
            db.session.commit()
            flash("Brand saved.", "success")
            return redirect(url_for("admin.brands"))
    return render_template("admin/brand_form.html", brand=b)


@admin_bp.route("/brands/<int:bid>/delete", methods=["POST"])
@admin_required
def brand_delete(bid):
    b = Brand.query.get_or_404(bid)
    db.session.delete(b)
    db.session.commit()
    flash("Brand deleted.", "info")
    return redirect(url_for("admin.brands"))


# --- Categories ---
@admin_bp.route("/categories")
@admin_required
def categories():
    q = Category.query
    if request.args.get("q"):
        q = q.filter(Category.name.ilike(f"%{request.args['q']}%"))
    items = q.order_by(Category.name).all()
    return render_template("admin/categories_list.html", items=items)


@admin_bp.route("/categories/new", methods=["GET", "POST"])
@admin_bp.route("/categories/<int:cid>/edit", methods=["GET", "POST"])
@admin_required
def category_form(cid=None):
    c = Category.query.get(cid) if cid else None
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        desc = request.form.get("description", "").strip()
        active = request.form.get("is_active") == "on"
        if not name:
            flash("Name required.", "danger")
        else:
            if not c:
                c = Category(name=name)
            c.name = name
            c.description = desc
            c.is_active = active
            db.session.add(c)
            db.session.commit()
            flash("Category saved.", "success")
            return redirect(url_for("admin.categories"))
    return render_template("admin/category_form.html", category=c)


@admin_bp.route("/categories/<int:cid>/delete", methods=["POST"])
@admin_required
def category_delete(cid):
    c = Category.query.get_or_404(cid)
    db.session.delete(c)
    db.session.commit()
    flash("Category deleted.", "info")
    return redirect(url_for("admin.categories"))


# --- Destinations ---
@admin_bp.route("/destinations")
@admin_required
def destinations():
    q = Destination.query
    if request.args.get("q"):
        q = q.filter(Destination.name.ilike(f"%{request.args['q']}%"))
    if request.args.get("state"):
        q = q.filter(Destination.state.ilike(f"%{request.args['state']}%"))
    if request.args.get("category_id", type=int):
        q = q.filter(Destination.category_id == request.args.get("category_id", type=int))
    items = q.order_by(Destination.name).all()
    cats = Category.query.filter_by(is_active=True).all()
    return render_template("admin/destinations_list.html", items=items, categories=cats)


@admin_bp.route("/destinations/new", methods=["GET", "POST"])
@admin_bp.route("/destinations/<int:did>/edit", methods=["GET", "POST"])
@admin_required
def destination_form(did=None):
    d = Destination.query.get(did) if did else None
    cats = Category.query.filter_by(is_active=True).all()
    if request.method == "POST":
        d = d or Destination()
        d.name = request.form.get("name", "").strip()
        d.state = request.form.get("state", "").strip()
        d.city = request.form.get("city", "").strip()
        d.short_description = request.form.get("short_description", "").strip()
        d.full_description = request.form.get("full_description", "").strip()
        d.best_season = request.form.get("best_season", "").strip()
        d.travel_duration_info = request.form.get("travel_duration_info", "").strip()
        d.category_id = request.form.get("category_id", type=int) or None
        img = save_upload(request.files.get("image"), "destinations")
        if img:
            d.image = img
        if not d.name:
            flash("Name required.", "danger")
        else:
            db.session.add(d)
            db.session.commit()
            flash("Destination saved.", "success")
            return redirect(url_for("admin.destinations"))
    return render_template("admin/destination_form.html", destination=d, categories=cats)


@admin_bp.route("/destinations/<int:did>/delete", methods=["POST"])
@admin_required
def destination_delete(did):
    d = Destination.query.get_or_404(did)
    db.session.delete(d)
    db.session.commit()
    flash("Destination deleted.", "info")
    return redirect(url_for("admin.destinations"))


# --- Hotels ---
@admin_bp.route("/hotels")
@admin_required
def hotels():
    items = Hotel.query.order_by(Hotel.name).all()
    return render_template("admin/hotels_list.html", items=items)


@admin_bp.route("/hotels/new", methods=["GET", "POST"])
@admin_bp.route("/hotels/<int:hid>/edit", methods=["GET", "POST"])
@admin_required
def hotel_form(hid=None):
    h = Hotel.query.get(hid) if hid else None
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Hotel name is required.", "danger")
        else:
            h = h or Hotel()
            h.name = name
            h.hotel_type = request.form.get("hotel_type", "").strip()
            h.room_type = request.form.get("room_type", "").strip()
            h.location = request.form.get("location", "").strip()
            h.description = request.form.get("description", "").strip()
            img = save_upload(request.files.get("image"), "hotels")
            if img:
                h.image = img
            db.session.add(h)
            db.session.commit()
            flash("Hotel saved.", "success")
            return redirect(url_for("admin.hotels"))
    return render_template("admin/hotel_form.html", hotel=h)


@admin_bp.route("/hotels/<int:hid>/delete", methods=["POST"])
@admin_required
def hotel_delete(hid):
    h = Hotel.query.get_or_404(hid)
    db.session.delete(h)
    db.session.commit()
    return redirect(url_for("admin.hotels"))


# --- Transport ---
@admin_bp.route("/transports")
@admin_required
def transports():
    items = Transport.query.order_by(Transport.id.desc()).all()
    return render_template("admin/transports_list.html", items=items)


@admin_bp.route("/transports/new", methods=["GET", "POST"])
@admin_bp.route("/transports/<int:tid>/edit", methods=["GET", "POST"])
@admin_required
def transport_form(tid=None):
    t = Transport.query.get(tid) if tid else None
    if request.method == "POST":
        t = t or Transport()
        t.transport_type = request.form.get("transport_type", "").strip()
        t.vehicle_details = request.form.get("vehicle_details", "").strip()
        t.seat_capacity = request.form.get("seat_capacity", type=int) or 0
        t.pickup_point = request.form.get("pickup_point", "").strip()
        t.description = request.form.get("description", "").strip()
        db.session.add(t)
        db.session.commit()
        flash("Transport saved.", "success")
        return redirect(url_for("admin.transports"))
    return render_template("admin/transport_form.html", transport=t)


@admin_bp.route("/transports/<int:tid>/delete", methods=["POST"])
@admin_required
def transport_delete(tid):
    t = Transport.query.get_or_404(tid)
    db.session.delete(t)
    db.session.commit()
    return redirect(url_for("admin.transports"))


# --- Packages ---
@admin_bp.route("/packages")
@admin_required
def packages():
    q = TourPackage.query
    if request.args.get("q"):
        q = q.filter(TourPackage.title.ilike(f"%{request.args['q']}%"))
    for key, field in [
        ("brand_id", TourPackage.brand_id),
        ("category_id", TourPackage.category_id),
        ("destination_id", TourPackage.destination_id),
    ]:
        v = request.args.get(key, type=int)
        if v:
            q = q.filter(field == v)
    if request.args.get("status"):
        q = q.filter(TourPackage.status == request.args["status"])
    items = q.order_by(TourPackage.created_at.desc()).all()
    brands = Brand.query.all()
    cats = Category.query.all()
    dests = Destination.query.all()
    return render_template(
        "admin/packages_list.html",
        items=items,
        brands=brands,
        categories=cats,
        destinations=dests,
    )


@admin_bp.route("/packages/new", methods=["GET", "POST"])
@admin_bp.route("/packages/<int:pid>/edit", methods=["GET", "POST"])
@admin_required
def package_form(pid=None):
    p = TourPackage.query.get(pid) if pid else None
    brands = Brand.query.filter_by(is_active=True).all()
    cats = Category.query.filter_by(is_active=True).all()
    dests = Destination.query.all()
    hotels = Hotel.query.order_by(Hotel.name).all()
    transports = Transport.query.all()
    if request.method == "POST":
        p = p or TourPackage()
        p.title = request.form.get("title", "").strip()
        p.brand_id = request.form.get("brand_id", type=int)
        p.category_id = request.form.get("category_id", type=int)
        p.destination_id = request.form.get("destination_id", type=int)
        p.hotel_id = request.form.get("hotel_id", type=int) or None
        p.transport_id = request.form.get("transport_id", type=int) or None
        p.price = request.form.get("price", type=float) or 0
        p.discount_price = request.form.get("discount_price", type=float) or None
        p.duration_days = request.form.get("duration_days", type=int) or 1
        p.duration_nights = request.form.get("duration_nights", type=int) or 0
        p.max_persons = request.form.get("max_persons", type=int) or 10
        p.start_point = request.form.get("start_point", "").strip()
        p.end_point = request.form.get("end_point", "").strip()
        p.hotel_details_text = request.form.get("hotel_details_text", "").strip()
        p.meal_details = request.form.get("meal_details", "").strip()
        p.transport_details_text = request.form.get("transport_details_text", "").strip()
        p.inclusions = request.form.get("inclusions", "").strip()
        p.exclusions = request.form.get("exclusions", "").strip()
        p.terms = request.form.get("terms", "").strip()
        p.status = request.form.get("status", "available")
        p.is_featured = request.form.get("is_featured") == "on"
        days = request.form.getlist("it_day")
        titles = request.form.getlist("it_title")
        descs = request.form.getlist("it_desc")
        it = []
        for i in range(len(days)):
            if str(days[i]).strip():
                it.append(
                    {
                        "day": days[i],
                        "title": titles[i] if i < len(titles) else "",
                        "description": descs[i] if i < len(descs) else "",
                    }
                )
        p.itinerary_json = json.dumps(it)
        main = save_upload(request.files.get("main_image"), "packages")
        if main:
            p.main_image = main
        if not p.title or not p.brand_id or not p.category_id or not p.destination_id:
            flash("Fill required fields.", "danger")
        else:
            db.session.add(p)
            db.session.commit()
            for f in request.files.getlist("gallery"):
                gp = save_upload(f, "packages/gallery")
                if gp:
                    db.session.add(PackageImage(package_id=p.id, image_path=gp))
            db.session.commit()
            flash("Package saved. You can add gallery images below.", "success")
            return redirect(url_for("admin.package_form", pid=p.id))
    itinerary = []
    if p and p.itinerary_json:
        try:
            itinerary = json.loads(p.itinerary_json)
        except json.JSONDecodeError:
            itinerary = []
    return render_template(
        "admin/package_form.html",
        package=p,
        brands=brands,
        categories=cats,
        destinations=dests,
        hotels=hotels,
        transports=transports,
        itinerary=itinerary,
    )


@admin_bp.route("/packages/<int:pid>")
@admin_required
def package_detail_admin(pid):
    p = TourPackage.query.get_or_404(pid)
    return render_template("admin/package_detail.html", package=p)


@admin_bp.route("/packages/<int:pid>/delete", methods=["POST"])
@admin_required
def package_delete(pid):
    p = TourPackage.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    flash("Package deleted.", "info")
    return redirect(url_for("admin.packages"))


@admin_bp.route("/package-images/<int:iid>/delete", methods=["POST"])
@admin_required
def package_image_delete(iid):
    img = PackageImage.query.get_or_404(iid)
    pid = img.package_id
    db.session.delete(img)
    db.session.commit()
    flash("Gallery image removed.", "success")
    return redirect(url_for("admin.package_form", pid=pid))


# --- Package dates ---
@admin_bp.route("/packages/<int:pid>/dates")
@admin_required
def package_dates(pid):
    p = TourPackage.query.get_or_404(pid)
    items = PackageDate.query.filter_by(package_id=p.id).order_by(PackageDate.travel_date).all()
    return render_template("admin/package_dates.html", package=p, dates=items)


@admin_bp.route("/packages/<int:pid>/dates/new", methods=["GET", "POST"])
@admin_bp.route("/package-dates/<int:did>/edit", methods=["GET", "POST"])
@admin_required
def package_date_form(pid=None, did=None):
    d = PackageDate.query.get(did) if did else None
    pkg_id = pid or (d.package_id if d else None)
    pkg = TourPackage.query.get_or_404(pkg_id)
    if request.method == "POST":
        d = d or PackageDate(package_id=pkg.id)
        d.travel_date = datetime.strptime(request.form.get("travel_date"), "%Y-%m-%d").date()
        d.seats_available = request.form.get("seats_available", type=int) or 0
        d.booking_closed = request.form.get("booking_closed") == "on"
        db.session.add(d)
        db.session.commit()
        flash("Date saved.", "success")
        return redirect(url_for("admin.package_dates", pid=pkg.id))
    return render_template("admin/package_date_form.html", package=pkg, date_row=d)


@admin_bp.route("/package-dates/<int:did>/delete", methods=["POST"])
@admin_required
def package_date_delete(did):
    d = PackageDate.query.get_or_404(did)
    pid = d.package_id
    db.session.delete(d)
    db.session.commit()
    return redirect(url_for("admin.package_dates", pid=pid))


# --- Users ---
@admin_bp.route("/users")
@admin_required
def users():
    q = User.query
    if request.args.get("q"):
        term = f"%{request.args['q']}%"
        q = q.filter(
            or_(User.full_name.ilike(term), User.email.ilike(term), User.mobile.ilike(term))
        )
    items = q.order_by(User.created_at.desc()).all()
    return render_template("admin/users_list.html", items=items)


@admin_bp.route("/users/<int:uid>")
@admin_required
def user_detail(uid):
    u = User.query.get_or_404(uid)
    bookings = Booking.query.filter_by(user_id=u.id).order_by(Booking.created_at.desc()).all()
    enquiries = Enquiry.query.filter_by(user_id=u.id).order_by(Enquiry.created_at.desc()).all()
    return render_template(
        "admin/user_detail.html", user=u, bookings=bookings, enquiries=enquiries
    )


@admin_bp.route("/users/<int:uid>/edit", methods=["GET", "POST"])
@admin_required
def user_edit(uid):
    u = User.query.get_or_404(uid)
    if request.method == "POST":
        u.full_name = request.form.get("full_name", u.full_name).strip()
        u.email = request.form.get("email", u.email).strip().lower()
        u.mobile = request.form.get("mobile", "").strip()
        u.address = request.form.get("address", "").strip()
        u.gender = request.form.get("gender", "").strip()
        u.is_active = request.form.get("is_active") == "on"
        db.session.commit()
        flash("User updated.", "success")
        return redirect(url_for("admin.user_detail", uid=u.id))
    return render_template("admin/user_edit.html", user=u)


@admin_bp.route("/users/<int:uid>/delete", methods=["POST"])
@admin_required
def user_delete(uid):
    u = User.query.get_or_404(uid)
    db.session.delete(u)
    db.session.commit()
    flash("User deleted.", "info")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:uid>/password", methods=["POST"])
@admin_required
def user_password_reset(uid):
    u = User.query.get_or_404(uid)
    newp = request.form.get("new_password", "").strip()
    if len(newp) < 6:
        flash("Password must be at least 6 characters.", "danger")
    else:
        u.set_password(newp)
        db.session.commit()
        flash("User password updated.", "success")
    return redirect(url_for("admin.user_detail", uid=u.id))


# --- Bookings ---
@admin_bp.route("/bookings")
@admin_required
def bookings():
    q = Booking.query
    if request.args.get("public_id"):
        q = q.filter(Booking.public_id.ilike(f"%{request.args['public_id']}%"))
    if request.args.get("status"):
        q = q.filter(Booking.status == request.args["status"])
    if request.args.get("user_id", type=int):
        q = q.filter(Booking.user_id == request.args.get("user_id", type=int))
    if request.args.get("package_id", type=int):
        q = q.filter(Booking.package_id == request.args.get("package_id", type=int))
    if request.args.get("payment_status"):
        q = q.filter(Booking.payment_status == request.args["payment_status"])
    df = request.args.get("date_from")
    dt = request.args.get("date_to")
    if df:
        q = q.filter(Booking.created_at >= datetime.strptime(df, "%Y-%m-%d"))
    if dt:
        end = datetime.strptime(dt, "%Y-%m-%d") + timedelta(days=1)
        q = q.filter(Booking.created_at < end)
    items = q.order_by(Booking.created_at.desc()).limit(500).all()
    return render_template("admin/bookings_list.html", items=items)


@admin_bp.route("/bookings/<int:bid>", methods=["GET", "POST"])
@admin_required
def booking_detail(bid):
    b = Booking.query.get_or_404(bid)
    if request.method == "POST":
        b.status = request.form.get("status", b.status)
        b.payment_status = request.form.get("payment_status", b.payment_status)
        b.admin_remarks = request.form.get("admin_remarks", "").strip()
        new_total = request.form.get("total_amount", type=float)
        if new_total is not None:
            b.total_amount = new_total
        new_date_id = request.form.get("package_date_id", type=int)
        if new_date_id and new_date_id != (b.package_date_id or 0):
            old = b.travel_slot
            new_slot = PackageDate.query.filter_by(
                id=new_date_id, package_id=b.package_id
            ).first()
            if new_slot and not new_slot.booking_closed:
                if old:
                    old.seats_available += b.travellers_count
                b.package_date_id = new_slot.id
                new_slot.seats_available = max(0, new_slot.seats_available - b.travellers_count)
        db.session.commit()
        flash("Booking updated.", "success")
        return redirect(url_for("admin.booking_detail", bid=b.id))
    dates = PackageDate.query.filter_by(package_id=b.package_id).order_by(
        PackageDate.travel_date
    ).all()
    travellers = b.travellers.order_by(BookingTraveller.id).all()
    payments = b.payments.order_by(Payment.created_at.desc()).all()
    total_paid = sum(
        float(p.amount or 0) for p in payments if (p.status or "") in ("paid", "partial")
    )
    balance = round(float(b.total_amount or 0) - total_paid, 2)
    return render_template(
        "admin/booking_detail.html",
        booking=b,
        package_dates=dates,
        travellers=travellers,
        payments=payments,
        total_paid=total_paid,
        balance=balance,
    )


@admin_bp.route("/bookings/<int:bid>/travellers", methods=["POST"])
@admin_required
def booking_travellers_update(bid):
    b = Booking.query.get_or_404(bid)
    BookingTraveller.query.filter_by(booking_id=b.id).delete()
    names = request.form.getlist("t_name")
    ages = request.form.getlist("t_age")
    genders = request.form.getlist("t_gender")
    proofs = request.form.getlist("t_proof")
    contacts = request.form.getlist("t_contact")
    for i in range(len(names)):
        db.session.add(
            BookingTraveller(
                booking_id=b.id,
                name=names[i],
                age=int(ages[i]) if i < len(ages) and ages[i] else None,
                gender=genders[i] if i < len(genders) else "",
                id_proof=proofs[i] if i < len(proofs) else "",
                contact=contacts[i] if i < len(contacts) else "",
            )
        )
    db.session.commit()
    flash("Travellers updated.", "success")
    return redirect(url_for("admin.booking_detail", bid=b.id))


@admin_bp.route("/bookings/<int:bid>/receipt")
@admin_required
def booking_receipt(bid):
    b = Booking.query.get_or_404(bid)
    return render_template("admin/booking_receipt.html", booking=b)


# --- Payments ---
@admin_bp.route("/payments")
@admin_required
def payments():
    q = Payment.query
    if request.args.get("booking"):
        q = q.join(Booking).filter(Booking.public_id.ilike(f"%{request.args['booking']}%"))
    if request.args.get("ref"):
        q = q.filter(Payment.reference_no.ilike(f"%{request.args['ref']}%"))
    if request.args.get("status"):
        q = q.filter(Payment.status == request.args["status"])
    items = q.order_by(Payment.created_at.desc()).limit(500).all()
    return render_template("admin/payments_list.html", items=items)


@admin_bp.route("/payments/new", methods=["GET", "POST"])
@admin_required
def payment_new():
    booking_id = request.args.get("booking_id", type=int)
    if request.method == "POST":
        booking_id = request.form.get("booking_id", type=int)
        p = Payment(
            booking_id=booking_id,
            amount=request.form.get("amount", type=float) or 0,
            mode=request.form.get("mode", "cash"),
            reference_no=request.form.get("reference_no", "").strip(),
            status=request.form.get("status", "paid"),
            notes=request.form.get("notes", "").strip() or None,
        )
        db.session.add(p)
        b = Booking.query.get(booking_id)
        if b:
            b.payment_status = request.form.get("booking_payment_status", b.payment_status)
        db.session.commit()
        flash("Payment recorded.", "success")
        return redirect(url_for("admin.payments"))
    bookings = Booking.query.order_by(Booking.created_at.desc()).limit(100).all()
    return render_template("admin/payment_form.html", booking_id=booking_id, bookings=bookings)


@admin_bp.route("/payments/<int:pid>/edit", methods=["GET", "POST"])
@admin_required
def payment_edit(pid):
    p = Payment.query.get_or_404(pid)
    if request.method == "POST":
        p.amount = request.form.get("amount", type=float) or p.amount
        p.mode = request.form.get("mode", p.mode)
        p.reference_no = request.form.get("reference_no", "").strip()
        p.status = request.form.get("status", p.status)
        p.notes = request.form.get("notes", "").strip() or None
        db.session.commit()
        flash("Payment updated.", "success")
        return redirect(url_for("admin.payments"))
    return render_template("admin/payment_edit.html", payment=p)


@admin_bp.route("/payments/<int:pid>/delete", methods=["POST"])
@admin_required
def payment_delete(pid):
    p = Payment.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    return redirect(url_for("admin.payments"))


@admin_bp.route("/payments/<int:pid>/receipt")
@admin_required
def payment_receipt(pid):
    p = Payment.query.get_or_404(pid)
    return render_template("admin/payment_receipt.html", payment=p)


# --- Enquiries ---
@admin_bp.route("/enquiries")
@admin_required
def enquiries():
    q = Enquiry.query
    if request.args.get("q"):
        term = f"%{request.args['q']}%"
        q = q.filter(or_(Enquiry.name.ilike(term), Enquiry.email.ilike(term)))
    if request.args.get("status"):
        q = q.filter(Enquiry.status == request.args["status"])
    items = q.order_by(Enquiry.created_at.desc()).limit(200).all()
    return render_template("admin/enquiries_list.html", items=items)


@admin_bp.route("/enquiries/<int:eid>", methods=["GET", "POST"])
@admin_required
def enquiry_detail(eid):
    e = Enquiry.query.get_or_404(eid)
    if request.method == "POST":
        e.is_read = request.form.get("is_read") == "on"
        e.admin_reply = request.form.get("admin_reply", "").strip()
        e.status = request.form.get("status", e.status)
        db.session.commit()
        flash("Enquiry updated.", "success")
        return redirect(url_for("admin.enquiry_detail", eid=e.id))
    return render_template("admin/enquiry_detail.html", enquiry=e)


@admin_bp.route("/enquiries/<int:eid>/delete", methods=["POST"])
@admin_required
def enquiry_delete(eid):
    e = Enquiry.query.get_or_404(eid)
    db.session.delete(e)
    db.session.commit()
    return redirect(url_for("admin.enquiries"))


# --- Reviews ---
@admin_bp.route("/reviews")
@admin_required
def reviews():
    q = Review.query
    if request.args.get("package_id", type=int):
        q = q.filter(Review.package_id == request.args.get("package_id", type=int))
    if request.args.get("rating", type=int):
        q = q.filter(Review.rating == request.args.get("rating", type=int))
    items = q.order_by(Review.created_at.desc()).limit(200).all()
    return render_template("admin/reviews_list.html", items=items)


@admin_bp.route("/reviews/<int:rid>/action", methods=["POST"])
@admin_required
def review_action(rid):
    r = Review.query.get_or_404(rid)
    r.is_approved = request.form.get("is_approved") == "on"
    r.is_hidden = request.form.get("is_hidden") == "on"
    db.session.commit()
    return redirect(url_for("admin.reviews"))


@admin_bp.route("/reviews/<int:rid>/delete", methods=["POST"])
@admin_required
def review_delete(rid):
    r = Review.query.get_or_404(rid)
    db.session.delete(r)
    db.session.commit()
    flash("Review deleted.", "info")
    return redirect(url_for("admin.reviews"))


@admin_bp.route("/reviews/<int:rid>/edit", methods=["GET", "POST"])
@admin_required
def review_edit(rid):
    r = Review.query.get_or_404(rid)
    if request.method == "POST":
        r.rating = max(1, min(5, request.form.get("rating", type=int) or r.rating))
        r.comment = request.form.get("comment", "").strip()
        r.is_approved = request.form.get("is_approved") == "on"
        r.is_hidden = request.form.get("is_hidden") == "on"
        db.session.commit()
        flash("Review updated.", "success")
        return redirect(url_for("admin.reviews"))
    return render_template("admin/review_form.html", review=r)


# --- Testimonials ---
@admin_bp.route("/testimonials")
@admin_required
def testimonials():
    items = Testimonial.query.order_by(Testimonial.id.desc()).all()
    return render_template("admin/testimonials_list.html", items=items)


@admin_bp.route("/testimonials/new", methods=["GET", "POST"])
@admin_bp.route("/testimonials/<int:tid>/edit", methods=["GET", "POST"])
@admin_required
def testimonial_form(tid=None):
    t = Testimonial.query.get(tid) if tid else None
    if request.method == "POST":
        t = t or Testimonial()
        t.customer_name = request.form.get("customer_name", "").strip()
        t.content = request.form.get("content", "").strip()
        t.is_visible = request.form.get("is_visible") == "on"
        img = save_upload(request.files.get("image"), "testimonials")
        if img:
            t.image = img
        db.session.add(t)
        db.session.commit()
        flash("Testimonial saved.", "success")
        return redirect(url_for("admin.testimonials"))
    return render_template("admin/testimonial_form.html", testimonial=t)


@admin_bp.route("/testimonials/<int:tid>/delete", methods=["POST"])
@admin_required
def testimonial_delete(tid):
    t = Testimonial.query.get_or_404(tid)
    db.session.delete(t)
    db.session.commit()
    return redirect(url_for("admin.testimonials"))


# --- Gallery ---
@admin_bp.route("/gallery")
@admin_required
def gallery():
    items = GalleryImage.query.order_by(GalleryImage.id.desc()).all()
    dests = Destination.query.all()
    pkgs = TourPackage.query.order_by(TourPackage.title).limit(100).all()
    return render_template("admin/gallery_list.html", items=items, destinations=dests, packages=pkgs)


@admin_bp.route("/gallery/new", methods=["GET", "POST"])
@admin_bp.route("/gallery/<int:gid>/edit", methods=["GET", "POST"])
@admin_required
def gallery_form(gid=None):
    g = GalleryImage.query.get(gid) if gid else None
    dests = Destination.query.all()
    pkgs = TourPackage.query.order_by(TourPackage.title).limit(100).all()
    if request.method == "POST":
        g = g or GalleryImage(image_path="")
        g.title = request.form.get("title", "").strip()
        g.destination_id = request.form.get("destination_id", type=int) or None
        g.package_id = request.form.get("package_id", type=int) or None
        g.is_visible = request.form.get("is_visible") == "on"
        img = save_upload(request.files.get("image"), "gallery")
        if img:
            g.image_path = img
        if not g.image_path:
            flash("Image required.", "danger")
        else:
            db.session.add(g)
            db.session.commit()
            return redirect(url_for("admin.gallery"))
    return render_template("admin/gallery_form.html", item=g, destinations=dests, packages=pkgs)


@admin_bp.route("/gallery/<int:gid>/delete", methods=["POST"])
@admin_required
def gallery_delete(gid):
    g = GalleryImage.query.get_or_404(gid)
    db.session.delete(g)
    db.session.commit()
    return redirect(url_for("admin.gallery"))


# --- Offers ---
@admin_bp.route("/offers")
@admin_required
def offers():
    items = Offer.query.order_by(Offer.id.desc()).all()
    pkgs = TourPackage.query.all()
    return render_template("admin/offers_list.html", items=items, packages=pkgs)


@admin_bp.route("/offers/new", methods=["GET", "POST"])
@admin_bp.route("/offers/<int:oid>/edit", methods=["GET", "POST"])
@admin_required
def offer_form(oid=None):
    o = Offer.query.get(oid) if oid else None
    pkgs = TourPackage.query.all()
    if request.method == "POST":
        o = o or Offer()
        o.title = request.form.get("title", "").strip()
        o.description = request.form.get("description", "").strip()
        o.discount_percent = request.form.get("discount_percent", type=float) or None
        o.discount_fixed = request.form.get("discount_fixed", type=float) or None
        o.package_id = request.form.get("package_id", type=int) or None
        sd = request.form.get("start_date")
        ed = request.form.get("end_date")
        o.start_date = datetime.strptime(sd, "%Y-%m-%d").date() if sd else None
        o.end_date = datetime.strptime(ed, "%Y-%m-%d").date() if ed else None
        o.is_active = request.form.get("is_active") == "on"
        db.session.add(o)
        db.session.commit()
        flash("Offer saved.", "success")
        return redirect(url_for("admin.offers"))
    return render_template("admin/offer_form.html", offer=o, packages=pkgs)


@admin_bp.route("/offers/<int:oid>/delete", methods=["POST"])
@admin_required
def offer_delete(oid):
    o = Offer.query.get_or_404(oid)
    db.session.delete(o)
    db.session.commit()
    return redirect(url_for("admin.offers"))


# --- Coupons ---
@admin_bp.route("/coupons")
@admin_required
def coupons():
    items = Coupon.query.order_by(Coupon.id.desc()).all()
    return render_template("admin/coupons_list.html", items=items)


@admin_bp.route("/coupons/new", methods=["GET", "POST"])
@admin_bp.route("/coupons/<int:cid>/edit", methods=["GET", "POST"])
@admin_required
def coupon_form(cid=None):
    c = Coupon.query.get(cid) if cid else None
    if request.method == "POST":
        c = c or Coupon(code=request.form.get("code", "").strip().upper())
        c.code = request.form.get("code", "").strip().upper()
        c.discount_type = request.form.get("discount_type", "percent")
        c.amount = request.form.get("amount", type=float) or 0
        c.min_booking_amount = request.form.get("min_booking_amount", type=float) or 0
        exp = request.form.get("expiry_date")
        c.expiry_date = datetime.strptime(exp, "%Y-%m-%d").date() if exp else None
        c.usage_limit = request.form.get("usage_limit", type=int) or 100
        c.is_active = request.form.get("is_active") == "on"
        db.session.add(c)
        db.session.commit()
        flash("Coupon saved.", "success")
        return redirect(url_for("admin.coupons"))
    return render_template("admin/coupon_form.html", coupon=c)


@admin_bp.route("/coupons/<int:cid>/delete", methods=["POST"])
@admin_required
def coupon_delete(cid):
    c = Coupon.query.get_or_404(cid)
    db.session.delete(c)
    db.session.commit()
    return redirect(url_for("admin.coupons"))


@admin_bp.route("/coupons/<int:cid>/usage")
@admin_required
def coupon_usage(cid):
    c = Coupon.query.get_or_404(cid)
    rows = CouponUsage.query.filter_by(coupon_id=c.id).all()
    return render_template("admin/coupon_usage.html", coupon=c, rows=rows)


# --- Static pages ---
@admin_bp.route("/pages")
@admin_required
def static_pages():
    items = StaticPage.query.order_by(StaticPage.slug).all()
    return render_template("admin/pages_list.html", items=items)


@admin_bp.route("/pages/new", methods=["GET", "POST"])
@admin_required
def static_page_new():
    if request.method == "POST":
        slug = request.form.get("slug", "").strip().lower().replace(" ", "-")
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        if not slug or not title:
            flash("Slug and title required.", "danger")
        elif StaticPage.query.filter_by(slug=slug).first():
            flash("That slug already exists.", "danger")
        else:
            p = StaticPage(slug=slug, title=title, content=content or "<p></p>")
            db.session.add(p)
            db.session.commit()
            flash("Page created.", "success")
            return redirect(url_for("admin.static_pages"))
    return render_template("admin/page_new.html")


@admin_bp.route("/pages/<slug>/edit", methods=["GET", "POST"])
@admin_required
def static_page_edit(slug):
    p = StaticPage.query.filter_by(slug=slug).first_or_404()
    if request.method == "POST":
        p.title = request.form.get("title", "").strip()
        p.content = request.form.get("content", "").strip()
        db.session.commit()
        flash("Page saved.", "success")
        return redirect(url_for("admin.static_pages"))
    return render_template("admin/page_edit.html", page=p)


# --- Homepage ---
@admin_bp.route("/homepage", methods=["GET", "POST"])
@admin_required
def homepage():
    sliders = Slider.query.order_by(Slider.sort_order).all()
    if request.method == "POST":
        for key in [
            "site_tagline",
            "banner_subtitle",
            "section_featured_title",
            "section_destinations_title",
            "section_offers_title",
            "section_testimonials_title",
            "section_brands_title",
            "section_gallery_title",
        ]:
            val = request.form.get(key, "")
            row = HomepageSetting.query.filter_by(key=key).first()
            if not row:
                row = HomepageSetting(key=key, value=val)
                db.session.add(row)
            else:
                row.value = val
        for sec in [
            "show_featured",
            "show_destinations",
            "show_offers",
            "show_testimonials",
            "show_brands",
            "show_gallery",
        ]:
            val = "1" if request.form.get(sec) == "on" else "0"
            row = HomepageSetting.query.filter_by(key=sec).first()
            if not row:
                db.session.add(HomepageSetting(key=sec, value=val))
            else:
                row.value = val
        db.session.commit()
        flash("Homepage settings saved.", "success")
        return redirect(url_for("admin.homepage"))
    return render_template("admin/homepage.html", sliders=sliders)


@admin_bp.route("/sliders/new", methods=["GET", "POST"])
@admin_bp.route("/sliders/<int:sid>/edit", methods=["GET", "POST"])
@admin_required
def slider_form(sid=None):
    s = Slider.query.get(sid) if sid else None
    if request.method == "POST":
        s = s or Slider(image="")
        s.headline = request.form.get("headline", "").strip()
        s.subheadline = request.form.get("subheadline", "").strip()
        s.link = request.form.get("link", "").strip()
        s.sort_order = request.form.get("sort_order", type=int) or 0
        s.is_active = request.form.get("is_active") == "on"
        img = save_upload(request.files.get("image"), "sliders")
        if img:
            s.image = img
        if not s.image:
            flash("Slider image required.", "danger")
        else:
            db.session.add(s)
            db.session.commit()
            return redirect(url_for("admin.homepage"))
    return render_template("admin/slider_form.html", slider=s)


@admin_bp.route("/sliders/<int:sid>/delete", methods=["POST"])
@admin_required
def slider_delete(sid):
    s = Slider.query.get_or_404(sid)
    db.session.delete(s)
    db.session.commit()
    return redirect(url_for("admin.homepage"))


# --- Reports ---
@admin_bp.route("/reports")
@admin_required
def reports():
    return render_template("admin/reports.html")


def _csv_response(filename, rows, header):
    si = io.StringIO()
    w = csv.writer(si)
    w.writerow(header)
    for r in rows:
        w.writerow(r)
    resp = make_response(si.getvalue())
    resp.headers["Content-Disposition"] = f"attachment; filename={filename}"
    resp.headers["Content-Type"] = "text/csv; charset=utf-8"
    return resp


@admin_bp.route("/reports/bookings.csv")
@admin_required
def report_bookings_csv():
    start = request.args.get("start")
    end = request.args.get("end")
    q = Booking.query
    if start:
        q = q.filter(Booking.created_at >= datetime.strptime(start, "%Y-%m-%d"))
    if end:
        q = q.filter(Booking.created_at <= datetime.strptime(end, "%Y-%m-%d"))
    rows = []
    for b in q.all():
        rows.append(
            [
                b.public_id,
                b.created_at.isoformat() if b.created_at else "",
                b.status,
                b.payment_status,
                float(b.total_amount or 0),
                b.package.title if b.package else "",
            ]
        )
    return _csv_response(
        "bookings.csv", rows, ["booking_id", "created", "status", "pay_status", "amount", "package"]
    )


@admin_bp.route("/reports/payments.csv")
@admin_required
def report_payments_csv():
    rows = []
    for p in Payment.query.all():
        rows.append(
            [
                p.booking.public_id if p.booking else "",
                float(p.amount or 0),
                p.mode,
                p.status,
                p.reference_no or "",
                p.created_at.isoformat() if p.created_at else "",
            ]
        )
    return _csv_response(
        "payments.csv", rows, ["booking_id", "amount", "mode", "status", "ref", "created"]
    )


@admin_bp.route("/reports/users.csv")
@admin_required
def report_users_csv():
    rows = [[u.full_name, u.email, u.mobile or "", u.created_at.isoformat() if u.created_at else ""] for u in User.query.all()]
    return _csv_response("users.csv", rows, ["name", "email", "mobile", "created"])
