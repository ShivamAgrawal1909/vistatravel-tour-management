"""
Populate the database with sample data for development/demo.
Run after creating MySQL database and configuring DATABASE_URL / default in config.py.

  python seed_data.py
"""

from datetime import date, timedelta

from app import create_app
from app.extensions import db
from app.models import (
    Admin,
    Booking,
    BookingTraveller,
    Brand,
    Category,
    Coupon,
    Destination,
    Enquiry,
    GalleryImage,
    HomepageSetting,
    Hotel,
    Offer,
    PackageDate,
    Review,
    Slider,
    StaticPage,
    Testimonial,
    TourPackage,
    Transport,
    User,
)
from config import Config


def seed():
    app = create_app(Config)
    with app.app_context():
        db.drop_all()
        db.create_all()

        admin = Admin(
            username="admin",
            email="admin@tourtravel.com",
            full_name="System Administrator",
        )
        admin.set_password("admin123")
        db.session.add(admin)

        categories_data = [
            ("Adventure", "High-energy outdoor experiences."),
            ("Family Tour", "Comfortable trips for all ages."),
            ("Hill Station", "Cool climate mountain getaways."),
            ("Religious Tour", "Pilgrimage and heritage circuits."),
            ("Honeymoon Tour", "Romantic escapes and private stays."),
            ("Wildlife", "National parks and safaris."),
            ("Cultural", "Heritage, food, and local immersion."),
            ("Beach", "Coastal resorts and water activities."),
        ]
        cats = []
        for name, desc in categories_data:
            c = Category(name=name, description=desc, is_active=True)
            db.session.add(c)
            cats.append(c)
        db.session.flush()

        brands_data = [
            ("Summit Trails", "Premium mountain expeditions."),
            ("Coastal Voyages", "Beach and island specialists."),
            ("Heritage Horizons", "Culture-first itineraries."),
            ("Family Fun Holidays", "Kid-friendly planning."),
            ("Sacred Journeys", "Pilgrimage logistics experts."),
            ("WildQuest Tours", "Wildlife-focused guides."),
            ("Azure Skies Travel", "Leisure and honeymoon."),
            ("Urban Escape Co.", "City breaks and events."),
        ]
        brands = []
        for name, desc in brands_data:
            b = Brand(name=name, description=desc, is_active=True)
            db.session.add(b)
            brands.append(b)
        db.session.flush()

        dest_specs = [
            ("Manali", "Himachal Pradesh", "Manali", cats[1]),
            ("Goa", "Goa", "Calangute", cats[7]),
            ("Jaipur", "Rajasthan", "Jaipur", cats[2]),
            ("Rishikesh", "Uttarakhand", "Rishikesh", cats[0]),
            ("Kerala Backwaters", "Kerala", "Alleppey", cats[4]),
            ("Agra", "Uttar Pradesh", "Agra", cats[3]),
            ("Darjeeling", "West Bengal", "Darjeeling", cats[2]),
            ("Andaman", "Andaman", "Port Blair", cats[7]),
        ]
        dests = []
        for name, state, city, cat in dest_specs:
            d = Destination(
                name=name,
                state=state,
                city=city,
                short_description=f"Explore {name} with curated experiences.",
                full_description=f"Full guide to {name} including highlights, best season, and travel tips.",
                best_season="Oct-Mar",
                travel_duration_info="4-7 days recommended",
                category_id=cat.id,
            )
            db.session.add(d)
            dests.append(d)
        db.session.flush()

        hotels = []
        for i in range(8):
            h = Hotel(
                name=f"Grand Stay {i+1}",
                hotel_type=f"{3 + (i % 3)} Star",
                room_type="Deluxe" if i % 2 == 0 else "Suite",
                location=dests[i].city,
                description="Complimentary breakfast, Wi-Fi, and airport transfers on request.",
            )
            db.session.add(h)
            hotels.append(h)
        db.session.flush()

        transports = []
        types = ["Bus", "Car", "Train", "Flight", "Bus", "Car", "Train", "Bus"]
        for i, t in enumerate(types):
            tr = Transport(
                transport_type=t,
                vehicle_details=f"{t} - AC, experienced driver",
                seat_capacity=20 + i * 5,
                pickup_point=dests[i].city + " city center",
            )
            db.session.add(tr)
            transports.append(tr)
        db.session.flush()

        package_titles = [
            "Himalayan Retreat - Manali",
            "Goa Sun & Sand Escape",
            "Royal Rajasthan Heritage",
            "Rishikesh Adventure Week",
            "Kerala Houseboat Romance",
            "Golden Triangle Classic",
            "Darjeeling Tea Trail",
            "Andaman Island Discovery",
        ]
        pkgs = []
        for i, title in enumerate(package_titles):
            p = TourPackage(
                title=title,
                brand_id=brands[i].id,
                category_id=cats[i % len(cats)].id,
                destination_id=dests[i].id,
                hotel_id=hotels[i].id,
                transport_id=transports[i].id,
                price=18000 + i * 2500,
                discount_price=16500 + i * 2300,
                duration_days=4 + (i % 4),
                duration_nights=3 + (i % 4),
                max_persons=8,
                start_point="Delhi" if i % 2 == 0 else "Mumbai",
                end_point=dests[i].name,
                hotel_details_text="Twin sharing, daily housekeeping.",
                meal_details="Breakfast + select dinners.",
                transport_details_text=transports[i].vehicle_details,
                itinerary_json='[{"day":"1","title":"Arrival","description":"Transfer and check-in"},{"day":"2","title":"Sightseeing","description":"Guided local tour"}]',
                inclusions="Hotels, meals as per plan, transfers, guide.",
                exclusions="Personal expenses, travel insurance.",
                terms="Standard cancellation policy applies.",
                main_image="img/placeholder.svg",
                status="available",
                is_featured=(i < 4),
            )
            db.session.add(p)
            pkgs.append(p)
        db.session.flush()

        for p in pkgs:
            for offset in (10, 24, 40):
                pd = PackageDate(
                    package_id=p.id,
                    travel_date=date.today() + timedelta(days=offset + p.id % 5),
                    seats_available=12,
                    booking_closed=False,
                )
                db.session.add(pd)
        db.session.flush()

        users = []
        for i in range(8):
            u = User(
                full_name=f"Demo User {i+1}",
                email=f"user{i+1}@demo.com",
                mobile=f"987654321{i}",
                address=f"{100+i} Demo Street",
                gender="Other" if i % 3 else "Male",
                is_active=True,
            )
            u.set_password("user123")
            db.session.add(u)
            users.append(u)
        db.session.flush()

        b0 = Booking(
            public_id="DEMO01AA",
            user_id=users[0].id,
            package_id=pkgs[0].id,
            package_date_id=PackageDate.query.filter_by(package_id=pkgs[0].id).first().id,
            travellers_count=2,
            total_amount=33000,
            status="confirmed",
            payment_status="paid",
            special_request="Window seats if possible.",
        )
        db.session.add(b0)
        db.session.flush()
        db.session.add(
            BookingTraveller(
                booking_id=b0.id, name="Demo User 1", age=32, gender="Male", contact="9876543210"
            )
        )
        db.session.add(
            BookingTraveller(
                booking_id=b0.id, name="Guest Two", age=30, gender="Female", contact="9876543211"
            )
        )

        for i in range(1, 4):
            slot = PackageDate.query.filter_by(package_id=pkgs[i].id).first()
            b = Booking(
                public_id=f"DEMO0{i+1}BB",
                user_id=users[i].id,
                package_id=pkgs[i].id,
                package_date_id=slot.id if slot else None,
                travellers_count=1,
                total_amount=float(pkgs[i].discount_price or pkgs[i].price),
                status="pending" if i == 1 else "confirmed",
                payment_status="pending" if i == 1 else "partial",
            )
            db.session.add(b)
        db.session.flush()

        db.session.add(
            Review(
                user_id=users[0].id,
                package_id=pkgs[0].id,
                rating=5,
                comment="Excellent coordination and hotels.",
                is_approved=True,
            )
        )

        for i in range(8):
            db.session.add(
                Testimonial(
                    customer_name=f"Happy Traveller {i+1}",
                    content=f"Our trip with {brands[i].name} was smooth and memorable.",
                    is_visible=True,
                )
            )

        for i in range(8):
            db.session.add(
                GalleryImage(
                    title=f"Highlight {i+1}",
                    image_path="img/placeholder.svg",
                    destination_id=dests[i].id,
                    is_visible=True,
                )
            )

        today = date.today()
        for i in range(8):
            db.session.add(
                Offer(
                    title=f"Season Special {i+1}",
                    description="Limited time discount on selected departures.",
                    discount_percent=10 + (i % 5),
                    package_id=pkgs[i].id,
                    start_date=today - timedelta(days=5),
                    end_date=today + timedelta(days=60),
                    is_active=True,
                )
            )

        coupons = [
            ("WELCOME10", "percent", 10, 5000),
            ("SAVE500", "fixed", 500, 8000),
            ("MONSOON15", "percent", 15, 12000),
            ("FAMILY20", "percent", 20, 20000),
            ("FLAT1000", "fixed", 1000, 15000),
            ("EARLY5", "percent", 5, 3000),
            ("VIP12", "percent", 12, 10000),
            ("NEWUSER8", "percent", 8, 6000),
        ]
        for code, dtype, amt, min_b in coupons:
            db.session.add(
                Coupon(
                    code=code,
                    discount_type=dtype,
                    amount=amt,
                    min_booking_amount=min_b,
                    expiry_date=today + timedelta(days=90),
                    usage_limit=50,
                    used_count=0,
                    is_active=True,
                )
            )

        pages = [
            ("about", "About Us", "<h2>Our story</h2><p>We craft reliable tours with transparent pricing.</p>"),
            ("contact", "Contact Us", "<p>Email: support@tourtravel.com<br>Phone: +91 1800-000-000</p>"),
            ("terms", "Terms & Conditions", "<p>Bookings subject to availability and these terms.</p>"),
            ("privacy", "Privacy Policy", "<p>We protect your personal data as per policy.</p>"),
            ("cancellation", "Cancellation Policy", "<p>Cancellation charges may apply by date.</p>"),
            ("faq", "FAQ", "<h3>How to book?</h3><p>Choose a package, date, and complete traveller details.</p>"),
        ]
        for slug, title, html in pages:
            db.session.add(StaticPage(slug=slug, title=title, content=html))

        db.session.add(
            Slider(
                image="img/placeholder.svg",
                headline="Discover your next journey",
                subheadline="Curated tours, trusted partners, seamless bookings.",
                link="/packages",
                sort_order=1,
                is_active=True,
            )
        )
        db.session.add(
            Slider(
                image="img/placeholder.svg",
                headline="Hill stations to coastlines",
                subheadline="Search packages by destination, budget, and travel style.",
                link="/destinations",
                sort_order=2,
                is_active=True,
            )
        )

        defaults = [
            ("site_tagline", "Premium tour & travel management"),
            ("banner_subtitle", "Plan smarter. Travel better."),
            ("section_featured_title", "Featured packages"),
            ("section_destinations_title", "Popular destinations"),
            ("section_offers_title", "Current offers"),
            ("section_testimonials_title", "What travellers say"),
            ("section_brands_title", "Partner brands"),
            ("section_gallery_title", "Gallery"),
            ("show_featured", "1"),
            ("show_destinations", "1"),
            ("show_offers", "1"),
            ("show_testimonials", "1"),
            ("show_brands", "1"),
            ("show_gallery", "1"),
        ]
        for k, v in defaults:
            db.session.add(HomepageSetting(key=k, value=v))

        db.session.add(
            Enquiry(
                name="Site Visitor",
                email="visitor@example.com",
                phone="9000000000",
                message="Looking for a family package in June.",
                enquiry_type="contact",
            )
        )

        db.session.commit()
        print("Seed completed.")
        print("Admin: username admin / password admin123")
        print("Users: user1@demo.com ... user8@demo.com / password user123")


if __name__ == "__main__":
    seed()
