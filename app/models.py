from datetime import datetime

from flask import current_app
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


def utcnow():
    return datetime.utcnow()


class Admin(db.Model):
    __tablename__ = "admin"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120))
    profile_image = db.Column(db.String(255))
    recovery_token = db.Column(db.String(128), index=True)
    recovery_token_expires = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    mobile = db.Column(db.String(20), index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    address = db.Column(db.Text)
    gender = db.Column(db.String(20))
    profile_image = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    recovery_token = db.Column(db.String(128), index=True)
    recovery_token_expires = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    bookings = db.relationship("Booking", backref="user", lazy="dynamic")
    wishlist_items = db.relationship("Wishlist", backref="user", lazy="dynamic", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Brand(db.Model):
    __tablename__ = "brands"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    logo = db.Column(db.String(255))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    packages = db.relationship("TourPackage", backref="brand", lazy="dynamic")


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    packages = db.relationship("TourPackage", backref="category", lazy="dynamic")


class Destination(db.Model):
    __tablename__ = "destinations"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False, index=True)
    state = db.Column(db.String(120), index=True)
    city = db.Column(db.String(120))
    short_description = db.Column(db.String(500))
    full_description = db.Column(db.Text)
    image = db.Column(db.String(255))
    best_season = db.Column(db.String(200))
    travel_duration_info = db.Column(db.String(300))
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    category = db.relationship("Category", backref="destinations")
    packages = db.relationship("TourPackage", backref="destination", lazy="dynamic")


class Hotel(db.Model):
    __tablename__ = "hotels"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    hotel_type = db.Column(db.String(80))
    room_type = db.Column(db.String(80))
    location = db.Column(db.String(255))
    description = db.Column(db.Text)
    image = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    packages = db.relationship("TourPackage", backref="hotel", lazy="dynamic")


class Transport(db.Model):
    __tablename__ = "transports"

    id = db.Column(db.Integer, primary_key=True)
    transport_type = db.Column(db.String(40), nullable=False)
    vehicle_details = db.Column(db.String(255))
    seat_capacity = db.Column(db.Integer, default=0)
    pickup_point = db.Column(db.String(255))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    packages = db.relationship("TourPackage", backref="transport", lazy="dynamic")


class TourPackage(db.Model):
    __tablename__ = "tour_packages"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    brand_id = db.Column(db.Integer, db.ForeignKey("brands.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    destination_id = db.Column(db.Integer, db.ForeignKey("destinations.id"), nullable=False)
    hotel_id = db.Column(db.Integer, db.ForeignKey("hotels.id"))
    transport_id = db.Column(db.Integer, db.ForeignKey("transports.id"))
    price = db.Column(db.Numeric(12, 2), nullable=False)
    discount_price = db.Column(db.Numeric(12, 2))
    duration_days = db.Column(db.Integer, default=1)
    duration_nights = db.Column(db.Integer, default=0)
    max_persons = db.Column(db.Integer, default=10)
    start_point = db.Column(db.String(255))
    end_point = db.Column(db.String(255))
    hotel_details_text = db.Column(db.Text)
    meal_details = db.Column(db.Text)
    transport_details_text = db.Column(db.Text)
    itinerary_json = db.Column(db.Text)
    inclusions = db.Column(db.Text)
    exclusions = db.Column(db.Text)
    terms = db.Column(db.Text)
    main_image = db.Column(db.String(255))
    status = db.Column(db.String(20), default="available")
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    images = db.relationship(
        "PackageImage", backref="package", lazy="dynamic", cascade="all, delete-orphan"
    )
    dates = db.relationship(
        "PackageDate", backref="package", lazy="dynamic", cascade="all, delete-orphan"
    )


class PackageImage(db.Model):
    __tablename__ = "package_images"

    id = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(db.Integer, db.ForeignKey("tour_packages.id"), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)


class PackageDate(db.Model):
    __tablename__ = "package_dates"

    id = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(db.Integer, db.ForeignKey("tour_packages.id"), nullable=False)
    travel_date = db.Column(db.Date, nullable=False)
    seats_available = db.Column(db.Integer, default=0)
    booking_closed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    __table_args__ = (db.UniqueConstraint("package_id", "travel_date", name="uq_pkg_date"),)


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(32), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    package_id = db.Column(db.Integer, db.ForeignKey("tour_packages.id"), nullable=False)
    package_date_id = db.Column(db.Integer, db.ForeignKey("package_dates.id"))
    travellers_count = db.Column(db.Integer, default=1)
    total_amount = db.Column(db.Numeric(12, 2), default=0)
    status = db.Column(db.String(20), default="pending")
    payment_status = db.Column(db.String(20), default="pending")
    special_request = db.Column(db.Text)
    admin_remarks = db.Column(db.Text)
    coupon_code = db.Column(db.String(40))
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    package = db.relationship("TourPackage", backref="bookings")
    travel_slot = db.relationship("PackageDate", backref="bookings")
    travellers = db.relationship(
        "BookingTraveller", backref="booking", lazy="dynamic", cascade="all, delete-orphan"
    )
    payments = db.relationship(
        "Payment", backref="booking", lazy="dynamic", cascade="all, delete-orphan"
    )


class BookingTraveller(db.Model):
    __tablename__ = "booking_travellers"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=False)
    name = db.Column(db.String(120))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    id_proof = db.Column(db.String(120))
    contact = db.Column(db.String(40))


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    mode = db.Column(db.String(40), nullable=False)
    reference_no = db.Column(db.String(120))
    status = db.Column(db.String(20), default="pending")
    proof_image = db.Column(db.String(255))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)


class Enquiry(db.Model):
    __tablename__ = "enquiries"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False, index=True)
    phone = db.Column(db.String(40))
    package_id = db.Column(db.Integer, db.ForeignKey("tour_packages.id"))
    message = db.Column(db.Text, nullable=False)
    enquiry_type = db.Column(db.String(40), default="contact")
    is_read = db.Column(db.Boolean, default=False)
    admin_reply = db.Column(db.Text)
    status = db.Column(db.String(20), default="open")
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    user = db.relationship("User", backref="enquiries")
    package = db.relationship("TourPackage", backref="enquiries")


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    package_id = db.Column(db.Integer, db.ForeignKey("tour_packages.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    is_approved = db.Column(db.Boolean, default=False)
    is_hidden = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    user = db.relationship("User", backref="reviews")
    package = db.relationship("TourPackage", backref="reviews")


class Testimonial(db.Model):
    __tablename__ = "testimonials"

    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(255))
    is_visible = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)


class GalleryImage(db.Model):
    __tablename__ = "gallery"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160))
    image_path = db.Column(db.String(255), nullable=False)
    destination_id = db.Column(db.Integer, db.ForeignKey("destinations.id"))
    package_id = db.Column(db.Integer, db.ForeignKey("tour_packages.id"))
    is_visible = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    destination = db.relationship("Destination", backref="gallery_items")
    package = db.relationship("TourPackage", backref="gallery_items")


class Offer(db.Model):
    __tablename__ = "offers"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text)
    discount_percent = db.Column(db.Numeric(5, 2))
    discount_fixed = db.Column(db.Numeric(12, 2))
    package_id = db.Column(db.Integer, db.ForeignKey("tour_packages.id"))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    package = db.relationship("TourPackage", backref="offers")


class Coupon(db.Model):
    __tablename__ = "coupons"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(40), unique=True, nullable=False, index=True)
    discount_type = db.Column(db.String(20), default="percent")
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    min_booking_amount = db.Column(db.Numeric(12, 2), default=0)
    expiry_date = db.Column(db.Date)
    usage_limit = db.Column(db.Integer, default=100)
    used_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)


class CouponUsage(db.Model):
    __tablename__ = "coupon_usage"

    id = db.Column(db.Integer, primary_key=True)
    coupon_id = db.Column(db.Integer, db.ForeignKey("coupons.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"))
    created_at = db.Column(db.DateTime, default=utcnow)

    coupon = db.relationship("Coupon", backref="usage_records")


class Wishlist(db.Model):
    __tablename__ = "wishlist"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    package_id = db.Column(db.Integer, db.ForeignKey("tour_packages.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    package = db.relationship("TourPackage", backref="wishlist_entries")

    __table_args__ = (db.UniqueConstraint("user_id", "package_id", name="uq_wishlist_user_pkg"),)


class StaticPage(db.Model):
    __tablename__ = "static_pages"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(64), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)


class Slider(db.Model):
    __tablename__ = "sliders"

    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(255), nullable=False)
    headline = db.Column(db.String(200))
    subheadline = db.Column(db.String(300))
    link = db.Column(db.String(255))
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)


class HomepageSetting(db.Model):
    __tablename__ = "homepage_settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    value = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)


class AdminNotification(db.Model):
    __tablename__ = "admin_notifications"

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(40), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    link = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utcnow)


def add_admin_notification(type_: str, message: str, link: str | None = None) -> None:
    try:
        n = AdminNotification(type=type_, message=message, link=link)
        db.session.add(n)
        db.session.commit()
    except Exception:
        db.session.rollback()
        if current_app:
            current_app.logger.exception("notification failed")
