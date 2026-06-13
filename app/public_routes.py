import json
from datetime import date, datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import or_

from .decorators import user_login_required
from .extensions import db
from .models import (
    Booking,
    BookingTraveller,
    Brand,
    Category,
    Coupon,
    CouponUsage,
    Destination,
    Enquiry,
    GalleryImage,
    Offer,
    PackageDate,
    Review,
    Slider,
    StaticPage,
    Testimonial,
    TourPackage,
)

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def home():
    sliders = Slider.query.filter_by(is_active=True).order_by(Slider.sort_order).all()
    featured = (
        TourPackage.query.filter_by(status="available", is_featured=True)
        .order_by(TourPackage.created_at.desc())
        .limit(6)
        .all()
    )
    latest = (
        TourPackage.query.filter_by(status="available")
        .order_by(TourPackage.created_at.desc())
        .limit(8)
        .all()
    )
    destinations = Destination.query.order_by(Destination.name).limit(8).all()
    testimonials = Testimonial.query.filter_by(is_visible=True).limit(6).all()
    brands = Brand.query.filter_by(is_active=True).order_by(Brand.name).all()
    today = date.today()
    offers = (
        Offer.query.filter(
            Offer.is_active == True,
            or_(Offer.start_date == None, Offer.start_date <= today),
            or_(Offer.end_date == None, Offer.end_date >= today),
        )
        .limit(6)
        .all()
    )
    gallery = GalleryImage.query.filter_by(is_visible=True).limit(12).all()
    return render_template(
        "public/home.html",
        sliders=sliders,
        featured_packages=featured,
        latest_packages=latest,
        destinations=destinations,
        testimonials=testimonials,
        brands=brands,
        offers=offers,
        gallery_preview=gallery,
    )


@public_bp.route("/packages")
def packages_list():
    q = TourPackage.query.filter_by(status="available")
    search = request.args.get("q", "").strip()
    brand_id = request.args.get("brand_id", type=int)
    category_id = request.args.get("category_id", type=int)
    destination_id = request.args.get("destination_id", type=int)
    min_p = request.args.get("min_price", type=float)
    max_p = request.args.get("max_price", type=float)
    min_d = request.args.get("min_days", type=int)
    max_d = request.args.get("max_days", type=int)
    travel_date = request.args.get("travel_date")
    featured_only = request.args.get("featured") == "1"
    sort = request.args.get("sort", "latest")

    if search:
        q = q.filter(TourPackage.title.ilike(f"%{search}%"))
    if brand_id:
        q = q.filter(TourPackage.brand_id == brand_id)
    if category_id:
        q = q.filter(TourPackage.category_id == category_id)
    if destination_id:
        q = q.filter(TourPackage.destination_id == destination_id)
    if min_p is not None:
        q = q.filter(TourPackage.price >= min_p)
    if max_p is not None:
        q = q.filter(TourPackage.price <= max_p)
    if min_d is not None:
        q = q.filter(TourPackage.duration_days >= min_d)
    if max_d is not None:
        q = q.filter(TourPackage.duration_days <= max_d)
    if featured_only:
        q = q.filter(TourPackage.is_featured == True)
    if travel_date:
        try:
            td = datetime.strptime(travel_date, "%Y-%m-%d").date()
            sub = db.session.query(PackageDate.package_id).filter(
                PackageDate.travel_date == td,
                PackageDate.booking_closed == False,
                PackageDate.seats_available > 0,
            )
            q = q.filter(TourPackage.id.in_(sub))
        except ValueError:
            pass

    if sort == "price_asc":
        q = q.order_by(TourPackage.price.asc())
    elif sort == "price_desc":
        q = q.order_by(TourPackage.price.desc())
    else:
        q = q.order_by(TourPackage.created_at.desc())

    page = request.args.get("page", 1, type=int)
    per_page = 12
    pagination = q.paginate(page=page, per_page=per_page)
    brands = Brand.query.filter_by(is_active=True).order_by(Brand.name).all()
    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
    destinations = Destination.query.order_by(Destination.name).all()
    return render_template(
        "public/packages.html",
        pagination=pagination,
        brands=brands,
        categories=categories,
        destinations=destinations,
    )


@public_bp.route("/packages/<int:pkg_id>")
def package_detail(pkg_id):
    pkg = TourPackage.query.get_or_404(pkg_id)
    if pkg.status != "available":
        flash("This package is not available.", "warning")
    reviews = (
        Review.query.filter_by(package_id=pkg.id, is_approved=True, is_hidden=False)
        .order_by(Review.created_at.desc())
        .all()
    )
    dates = (
        PackageDate.query.filter_by(package_id=pkg.id, booking_closed=False)
        .filter(PackageDate.seats_available > 0)
        .filter(PackageDate.travel_date >= date.today())
        .order_by(PackageDate.travel_date)
        .all()
    )
    avg = db.session.query(db.func.avg(Review.rating)).filter(
        Review.package_id == pkg.id, Review.is_approved == True, Review.is_hidden == False
    ).scalar()
    itinerary = []
    if pkg.itinerary_json:
        try:
            itinerary = json.loads(pkg.itinerary_json)
        except json.JSONDecodeError:
            itinerary = []
    return render_template(
        "public/package_detail.html",
        package=pkg,
        reviews=reviews,
        available_dates=dates,
        avg_rating=float(avg) if avg else None,
        itinerary=itinerary,
    )


@public_bp.route("/destinations")
def destinations_list():
    q = Destination.query
    search = request.args.get("q", "").strip()
    state = request.args.get("state", "").strip()
    cat_id = request.args.get("category_id", type=int)
    if search:
        q = q.filter(Destination.name.ilike(f"%{search}%"))
    if state:
        q = q.filter(Destination.state.ilike(f"%{state}%"))
    if cat_id:
        q = q.filter(Destination.category_id == cat_id)
    items = q.order_by(Destination.name).all()
    categories = Category.query.filter_by(is_active=True).all()
    return render_template(
        "public/destinations.html", destinations=items, categories=categories
    )


@public_bp.route("/destinations/<int:dest_id>")
def destination_detail(dest_id):
    d = Destination.query.get_or_404(dest_id)
    pkgs = TourPackage.query.filter_by(destination_id=d.id, status="available").all()
    return render_template("public/destination_detail.html", destination=d, packages=pkgs)


@public_bp.route("/gallery")
def gallery_page():
    items = GalleryImage.query.filter_by(is_visible=True).order_by(GalleryImage.id.desc()).all()
    return render_template("public/gallery.html", items=items)


@public_bp.route("/offers")
def offers_page():
    today = date.today()
    items = Offer.query.filter(
        Offer.is_active == True,
        or_(Offer.start_date == None, Offer.start_date <= today),
        or_(Offer.end_date == None, Offer.end_date >= today),
    ).all()
    return render_template("public/offers.html", offers=items)


@public_bp.route("/page/<slug>")
def static_page(slug):
    page = StaticPage.query.filter_by(slug=slug).first_or_404()
    return render_template("public/static_page.html", page=page)


@public_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        message = request.form.get("message", "").strip()
        if not name or not email or not message:
            flash("Please fill required fields.", "danger")
        else:
            enq = Enquiry(
                name=name,
                email=email,
                phone=phone,
                message=message,
                enquiry_type="contact",
            )
            db.session.add(enq)
            db.session.commit()
            from .models import add_admin_notification

            add_admin_notification("enquiry", f"New contact message from {name}", "/admin/enquiries")
            flash("Thank you. We will get back to you soon.", "success")
            return redirect(url_for("public.contact"))
    return render_template("public/contact.html")


@public_bp.route("/enquiry/package/<int:pkg_id>", methods=["GET", "POST"])
@user_login_required
def package_enquiry(pkg_id):
    from flask import session

    pkg = TourPackage.query.get_or_404(pkg_id)
    user_id = session.get("user_id")
    from .models import User

    user = User.query.get(user_id)
    if request.method == "POST":
        message = request.form.get("message", "").strip()
        if not message:
            flash("Please enter your message.", "danger")
        else:
            enq = Enquiry(
                user_id=user_id,
                name=user.full_name,
                email=user.email,
                phone=user.mobile or "",
                package_id=pkg.id,
                message=message,
                enquiry_type="package",
            )
            db.session.add(enq)
            db.session.commit()
            from .models import add_admin_notification

            add_admin_notification(
                "enquiry", f"Package enquiry: {pkg.title}", f"/admin/enquiries"
            )
            flash("Enquiry submitted.", "success")
            return redirect(url_for("public.package_detail", pkg_id=pkg.id))
    return render_template("public/package_enquiry.html", package=pkg, user=user)


@public_bp.route("/book/<int:pkg_id>", methods=["GET", "POST"])
@user_login_required
def book_package(pkg_id):
    from flask import session

    from .models import User
    from .utils import generate_public_booking_id

    pkg = TourPackage.query.get_or_404(pkg_id)
    user = User.query.get(session["user_id"])
    dates = (
        PackageDate.query.filter_by(package_id=pkg.id, booking_closed=False)
        .filter(PackageDate.seats_available > 0)
        .filter(PackageDate.travel_date >= date.today())
        .order_by(PackageDate.travel_date)
        .all()
    )
    if request.method == "POST":
        date_id = request.form.get("package_date_id", type=int)
        travellers_count = request.form.get("travellers_count", type=int) or 1
        special = request.form.get("special_request", "").strip()
        coupon_code = request.form.get("coupon_code", "").strip().upper()

        slot = PackageDate.query.filter_by(
            id=date_id, package_id=pkg.id, booking_closed=False
        ).first()
        if not slot or travellers_count < 1:
            flash("Invalid selection.", "danger")
            return redirect(url_for("public.book_package", pkg_id=pkg.id))
        if travellers_count > pkg.max_persons:
            flash(f"Maximum {pkg.max_persons} travellers allowed.", "danger")
            return redirect(url_for("public.book_package", pkg_id=pkg.id))
        if slot.seats_available < travellers_count:
            flash("Not enough seats for this date.", "danger")
            return redirect(url_for("public.book_package", pkg_id=pkg.id))

        unit = float(pkg.discount_price or pkg.price)
        total = unit * travellers_count
        applied_coupon = None
        if coupon_code:
            c = Coupon.query.filter_by(code=coupon_code, is_active=True).first()
            if (
                c
                and (c.expiry_date is None or c.expiry_date >= date.today())
                and (c.usage_limit is None or c.used_count < c.usage_limit)
                and float(total) >= float(c.min_booking_amount or 0)
            ):
                applied_coupon = c
                if c.discount_type == "percent":
                    total = total * (1 - float(c.amount) / 100)
                else:
                    total = max(0, total - float(c.amount))
            else:
                flash("Coupon could not be applied.", "warning")

        booking = Booking(
            public_id=generate_public_booking_id(),
            user_id=user.id,
            package_id=pkg.id,
            package_date_id=slot.id,
            travellers_count=travellers_count,
            total_amount=round(total, 2),
            status="pending",
            payment_status="pending",
            special_request=special,
            coupon_code=applied_coupon.code if applied_coupon else None,
        )
        db.session.add(booking)
        db.session.flush()

        for i in range(travellers_count):
            prefix = f"t_{i}_"
            tname = request.form.get(prefix + "name", "").strip() or f"Traveller {i+1}"
            tage = request.form.get(prefix + "age", type=int)
            tgender = request.form.get(prefix + "gender", "").strip()
            tid = request.form.get(prefix + "id_proof", "").strip()
            tcontact = request.form.get(prefix + "contact", "").strip()
            db.session.add(
                BookingTraveller(
                    booking_id=booking.id,
                    name=tname,
                    age=tage,
                    gender=tgender,
                    id_proof=tid,
                    contact=tcontact,
                )
            )

        if applied_coupon:
            applied_coupon.used_count = (applied_coupon.used_count or 0) + 1
            db.session.add(
                CouponUsage(coupon_id=applied_coupon.id, user_id=user.id, booking_id=booking.id)
            )

        slot.seats_available -= travellers_count
        db.session.commit()

        from .models import add_admin_notification

        add_admin_notification(
            "booking",
            f"New booking {booking.public_id} for {pkg.title}",
            f"/admin/bookings/{booking.id}",
        )
        flash("Booking created. Complete payment from your dashboard.", "success")
        return redirect(url_for("user.booking_detail", booking_id=booking.id))

    return render_template(
        "public/book.html", package=pkg, user=user, available_dates=dates
    )


@public_bp.route("/coupon/check", methods=["POST"])
def coupon_check():
    """AJAX-friendly simple check — returns redirect not needed; used optional."""
    return redirect(request.referrer or url_for("public.home"))
