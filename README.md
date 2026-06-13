# VistaTravel — Tour & Travel Management System

A full-stack **tour and travel** web application built with **Flask**, **SQLAlchemy**, and **Bootstrap 5**. It provides a public marketing and booking site for visitors, a **customer portal** for logged-in users, and an **admin operations console** for staff to manage catalog, bookings, payments, and content.

---

## Tech stack

| Layer | Technology |
|--------|------------|
| Framework | Flask 3.x |
| ORM | Flask-SQLAlchemy 3.x |
| Database (default) | MySQL 8.x via **PyMySQL** |
| Config | `python-dotenv` (optional `.env`) |
| Frontend | Jinja2 templates, Bootstrap 5, Bootstrap Icons |
| Passwords | Werkzeug password hashing |

---

## Project structure (high level)

```
Tour and Travel/
├── run.py                 # App entry: debug server on port 5000
├── config.py              # Config class: SECRET_KEY, DATABASE_URL, uploads
├── seed_data.py           # Demo data (drops & recreates all tables)
├── requirements.txt
├── app/
│   ├── __init__.py        # create_app(), blueprints, db.create_all()
│   ├── models.py          # SQLAlchemy models
│   ├── extensions.py      # db
│   ├── decorators.py      # login / admin guards
│   ├── utils.py           # uploads, tokens, booking IDs
│   ├── public_routes.py   # Public site (blueprint: no prefix)
│   ├── auth_routes.py     # /auth — register, login, logout, password recovery
│   ├── user_routes.py     # /user — customer dashboard & tools
│   ├── admin_auth.py      # /admin — admin login, profile, password
│   ├── admin_routes.py    # /admin — admin CRUD & reports
│   ├── templates/         # Jinja HTML
│   └── static/            # CSS, JS, uploads folder
```

Uploaded files are stored under `app/static/uploads/` (created automatically if missing).

---

## Public site functionality

- **Home** — Hero sliders, featured & latest packages, destinations, offers, testimonials, brands, gallery preview.
- **Packages** — Search and filter by brand, category, destination, price range, duration, travel date, featured flag; sorting and pagination.
- **Package detail** — Pricing, itinerary, inclusions/exclusions, available departure dates, approved reviews, booking CTA.
- **Destinations** — List and detail with related packages.
- **Gallery, Offers** — Browse promotional and media content.
- **Static CMS pages** — e.g. About, FAQ, Terms (`/page/<slug>`).
- **Contact form** — Creates enquiries and notifies admin.
- **Booking flow** (`/book/<package_id>`) — Requires user login. Select date, traveller count, traveller details, optional **coupon**; creates booking, reduces seat availability, notifies admin.

---

## User (customer) functionality

Base URL: **`/user`** (after login). Auth: **`/auth`**.

| Area | Description |
|------|-------------|
| **Register / Login / Logout** | Email + password; inactive users cannot sign in. |
| **Forgot password** | Token-based reset (see `auth_routes`). |
| **Dashboard** | Stats: bookings, wishlist, open enquiries, pending payments; upcoming trip highlight. |
| **Profile** | Update name, mobile, address, gender; optional profile image upload. |
| **Change password** | Current password + new password (min 6 characters). |
| **Bookings** | List; open **booking detail** with travellers, payments, balance. |
| **Receipt** | Printable booking receipt. |
| **Cancel booking** | Allowed unless already cancelled/completed; restores seats; notifies admin. |
| **Submit payment** | Amount, mode, reference, optional proof image (pending until admin confirms). |
| **Wishlist** | Add/remove packages. |
| **Reviews** | After a **confirmed or completed** booking for a package, user can submit/edit a review (pending admin approval). |
| **Enquiries** | Logged-in user enquiries tied to account; **package enquiry** from package page. |

---

## Admin functionality

Admin UI is under **`/admin`** (same path prefix as admin auth).

**Sign-in:** `/admin/login` (username **or** email + password).

### Operations & catalog

- **Dashboard** — KPIs, booking/payment summaries, notifications, recent activity.
- **Brands, Categories, Destinations** — Full CRUD.
- **Hotels, Transports** — Master data CRUD for packages.
- **Tour packages** — Create/edit: mapping, pricing, copy, main image, **gallery** (per-image delete), day-wise itinerary JSON; **package dates** (seats, open/closed); delete package.
- **Users** — Search, view profile, edit, **reset password**, delete; see user bookings and enquiries.

### Bookings & money

- **Bookings** — Filter by status, payment status, user/package IDs, date range; open **booking detail**: update status, payment status, travel slot, total, remarks; **traveller manifest**; **payments** list with edit/delete; record new payment; receipts.

- **Payments** — Ledger with filters; create/edit/delete; internal **notes**; optional receipt.

### CRM & moderation

- **Enquiries** — List, filter, detail (read flag, reply, status), delete.
- **Reviews** — Approve/hide flags, edit text/rating, delete.

### Marketing & content

- **Testimonials, Gallery images, Offers, Coupons** — CRUD; coupon usage report.
- **Static pages** — List, **create** (slug + HTML), edit.
- **Homepage** — Section titles and related settings.
- **Hero sliders** — CRUD.
- **Reports** — Booking / payment / user **CSV** exports.

### Admin account

- **Profile** and **change password** (routes in `admin_auth` under `/admin`).

---

## Prerequisites

- **Python 3.10+** (recommended)
- **MySQL 5.5.3+** or **MySQL 8.x** / **MariaDB** (with `utf8mb4`) if you use a MySQL connection string
- `pip` for dependencies

---

## Setup: Python environment

```bash
cd "path/to/Tour and Travel"
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

---

## Setup: database

### Option A — MySQL / MariaDB (default in `config.py`)

1. Install and start **MySQL** or **MariaDB**. Managing users and permissions via **MySQL Workbench**, **phpMyAdmin**, or the CLI all work the same; the app only needs a valid SQLAlchemy database URL.

2. **Database creation (optional):** On first startup the app runs **`CREATE DATABASE IF NOT EXISTS`** for the name in your URL (e.g. `tour_travel_db`) using `utf8mb4` / `utf8mb4_unicode_ci`, compatible with **MySQL 5.5.3+** and **MySQL 8**. You can still create the database yourself if you prefer:

   ```sql
   CREATE DATABASE tour_travel_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

3. Ensure the MySQL user can connect from your host and **create the database** (for auto-create) or **use** an existing database.

4. Set the connection string in `config.py` or via **`DATABASE_URL`** (recommended for production):

   ```env
   DATABASE_URL=mysql+pymysql://USER:PASSWORD@127.0.0.1:3306/tour_travel_db?charset=utf8
   ```

   On **MySQL 5.5.3+** or **MySQL 8**, you may use `charset=utf8mb4` in the URL for full Unicode (e.g. emoji). Older MySQL (before 5.5.3) does not support `utf8mb4`; use **`charset=utf8`** or you will see `Unknown character set: 'utf8mb4'`.

5. Optional `.env` in the project root (loaded by `config.py`):

   ```env
   SECRET_KEY=your-long-random-secret
   DATABASE_URL=mysql+pymysql://USER:PASSWORD@127.0.0.1:3306/tour_travel_db?charset=utf8
   ```

On first startup, `create_app()` ensures the MySQL database exists (if using a MySQL driver), then runs **`db.create_all()`** to create tables. For a full **demo dataset**, use the seed script (below).

### Option B — SQLite (quick local testing)

Point `DATABASE_URL` to a SQLite file (no PyMySQL needed for the DB file itself; `PyMySQL` remains in `requirements.txt` but is unused if the URI is SQLite):

```env
DATABASE_URL=sqlite:///tour_travel.db
```

Use the same `seed_data.py` flow; ensure the SQLite file path is writable.

---

## Demo data & default credentials

The seed script **drops all tables** and recreates them, then inserts sample brands, categories, destinations, packages, bookings, etc.

```bash
python seed_data.py
```

### Administrator (back office)

| Field | Value |
|--------|--------|
| **URL** | http://127.0.0.1:5000/admin/login |
| **Username** | `admin` |
| **Password** | `admin123` |
| **Email (also accepted as login)** | `admin@tourtravel.com` |

### Demo customers (after seed)

| Email | Password |
|--------|----------|
| `user1@demo.com` … `user8@demo.com` | `user123` |

Use **`/auth/login`** for customers and **`/admin/login`** for staff (different sessions).

---

## How to run

From the project root (with venv activated and database reachable):

```bash
python run.py
```

- **URL:** http://127.0.0.1:5000  
- **Debug:** enabled in `run.py` (disable in production and use a proper WSGI server).

Production-oriented run (example with Gunicorn, not in `requirements.txt`):

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "run:app"
```

---

## Configuration reference (`config.py`)

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | Flask session signing; change in production. |
| `SQLALCHEMY_DATABASE_URI` | From env `DATABASE_URL` or MySQL default above. |
| `UPLOAD_FOLDER` | `app/static/uploads` |
| `MAX_CONTENT_LENGTH` | 16 MB upload limit |
| `PER_PAGE` | Public listing page size (e.g. 12) |

---

## License
This project is for educational and portfolio purposes only.
