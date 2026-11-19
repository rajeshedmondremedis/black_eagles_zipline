# BLACK EAGLES ZIPLINE – WEBSITE & ONLINE SLOT BOOKING SYSTEM
### Developed by PL SOFT TECH SOLUTIONS

---

## 1. Project Overview

**Black Eagles Zipline** is a commercial-grade adventure tourism web platform featuring a real-time, date-based zipline slot reservation engine and administrative operations portal.

### Key Capabilities:
- **Cinematic Adventure Experience Website:** Dark forest green & warm amber visual theme, responsive gallery with lightbox, about story, pricing tiers, safety guidelines, and interactive contact location map.
- **Online Slot Booking Engine:**
  - Strict date validation: past dates automatically blocked.
  - Automatic Wednesday closures for structural line inspections.
  - Dynamic admin-defined holiday blackout dates.
  - **4 Configurable Daily Operating Slots** (Default 6 pax max capacity each, 24 daily maximum).
  - Real-time seat calculation: $\text{Available Seats} = \text{Capacity} - \text{Confirmed Members}$.
  - Fully booked slots ($\text{Available Seats} = 0$) are hidden automatically from customer view.
  - Supports multiple groups sharing a slot up to capacity.
  - Number of members restricted to 1–6 riders.
  - **Database-Level Concurrency Protection:** Utilizes Django's `transaction.atomic()` and `select_for_update()` row locks to prevent simultaneous double-booking overages.
  - Generates unique sequential booking references (e.g. `BEZ-2026-000001`).
  - Printable boarding vouchers (`window.print()`).
  - Asynchronous email notifications (configurable SMTP / console backend).
- **Custom Admin Operations Dashboard:**
  - Modern tablet/desktop responsive dark sidebar layout.
  - KPI overview: Total bookings, Today's bookings, Upcoming reservations, Confirmed pax, Slot occupancy rates, Chart.js 7-day trend.
  - Full booking search (reference, name, phone, email, place) and multi-parameter filters (date, slot, status).
  - Reschedule / modify reservations and cancel bookings (with capacity release back into the slot pool).
  - Comprehensive chronological audit trail logging (`BookingAuditLog`).
  - Daily slot manager: update names, timings, capacity, toggle pause/active with safety checks preventing lowering capacity below confirmed riders.
  - Holiday calendar with conflict warnings when bookings already exist on the proposed date.
  - **OpenPyXL Excel Manifest Export** with styled headers and totals.
  - **ReportLab PDF Passenger Manifest Export** with company branding.
  - Zero-code content manager for Site Settings, Pricing Tiers, Safety Protocols, and Media Gallery.

---

## 2. Technology Stack

- **Backend:** Python 3.12+ / Django 5.x / 6.x
- **Database:** MySQL 8.x (production-ready) with SQLite3 local dev fallback
- **Frontend:** HTML5, CSS3, Bootstrap 5.3.3, Bootstrap Icons, JavaScript (Fetch API / AJAX)
- **Document Generators:** `openpyxl` (Excel .xlsx), `reportlab` (PDF .pdf)
- **Image Processing:** `Pillow`
- **Application Server & Proxy:** Gunicorn (WSGI) + Nginx (Reverse Proxy)

---

## 3. Project Architecture

```
black_eagles_zipline/
├── manage.py
├── .env.example
├── .env
├── requirements.txt
├── README.md
├── gunicorn_config.py
├── nginx.conf
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── core/              # SiteSettings singleton, seed_data command, context processors
│   ├── website/           # GalleryImage, SafetyGuideline, PricingPackage, ContactMessage
│   ├── bookings/          # BookingSlot, Holiday, Booking, BookingAuditLog, atomic services
│   ├── dashboard/         # Custom admin portal views and management consoles
│   └── reports/           # Excel & PDF export engines
├── templates/
│   ├── base.html
│   ├── components/        # navbar, footer, alerts
│   ├── website/           # home, about, gallery, safety, pricing, contact
│   ├── bookings/          # booking_page, booking_success
│   ├── dashboard/         # base_dashboard, login, index, bookings_list, detail, slots, holidays, reports...
│   └── emails/            # HTML & plaintext confirmation emails
├── static/
│   ├── css/               # style.css, dashboard.css
│   ├── js/                # main.js, booking.js, dashboard.js
│   └── images/            # hero-zipline.jpg, icons
└── media/
    └── gallery/           # Action photographs
```

---

## 4. Installation & Local Setup

### Step 1: Clone or Navigate to Directory
```bash
cd c:\Users\rajesh\Downloads\project\black_eagles_zipline
```

### Step 2: Create and Activate Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
For local testing, the default `DB_ENGINE=django.db.backends.sqlite3` works out of the box.

---

## 5. MySQL 8.x Database Configuration (Production)

To connect to MySQL 8.x, create a database and update your `.env`:

```sql
CREATE DATABASE black_eagles_zipline CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'zipline_admin'@'localhost' IDENTIFIED BY 'YourStrongPassword123!';
GRANT ALL PRIVILEGES ON black_eagles_zipline.* TO 'zipline_admin'@'localhost';
FLUSH PRIVILEGES;
```

In `.env`:
```ini
DB_ENGINE=django.db.backends.mysql
DB_NAME=black_eagles_zipline
DB_USER=zipline_admin
DB_PASSWORD=YourStrongPassword123!
DB_HOST=127.0.0.1
DB_PORT=3306
```

---

## 6. Database Migrations & Initial Seeding

Apply database schema migrations:
```bash
python manage.py migrate
```

Seed initial data (creates admin superuser, 4 operating slots, site configuration, safety protocols, pricing packages, and gallery records):
```bash
python manage.py seed_data
```

### Default Initial Credentials:
- **Admin Portal URL:** `http://127.0.0.1:8000/admin-panel/login/`
- **Username:** `admin`
- **Password:** `admin123`
*(Please change password upon production deployment)*

---

## 7. Starting the Development Server

```bash
python manage.py runserver
```
- Public Customer Website: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- Customer Booking Page: [http://127.0.0.1:8000/book/](http://127.0.0.1:8000/book/)
- Admin Operations Portal: [http://127.0.0.1:8000/admin-panel/login/](http://127.0.0.1:8000/admin-panel/login/)

---

## 8. Running Automated Test Suites

The project includes automated test coverage verifying all 21 acceptance criteria scenarios:

```bash
python manage.py test apps.website apps.bookings apps.dashboard apps.reports
```

### Verified Test Matrix:
1. `test_01_customer_can_open_website` – Public homepage loads with branding.
2. `test_02_customer_can_access_booking_page` – Booking form renders.
3. `test_03_customer_can_select_valid_date` – Real-time availability returns valid slots.
4. `test_04_wednesday_booking_is_blocked` – Wednesday bookings rejected at API & service level.
5. `test_05_past_date_booking_is_blocked` – Historical dates prevented.
6. `test_06_admin_defined_holiday_booking_is_blocked` – Admin holidays return closure message.
7. `test_07_available_slots_are_displayed` – Slots with remaining capacity listed.
8. `test_08_fully_booked_slots_are_hidden` – Slots with 0 seats hidden from customers.
9. `test_09_booking_for_one_member_works` – 1-pax solo flight succeeds.
10. `test_10_booking_for_six_members_works_when_capacity_available` – 6-pax group succeeds.
11. `test_11_booking_for_more_than_six_members_is_rejected` – >6 pax strictly rejected.
12. `test_12_insufficient_remaining_capacity_is_rejected` – Over-capacity attempts fail.
13. `test_13_cancelled_booking_releases_seats` – Cancellation restores slot capacity.
14. `test_14_modified_booking_updates_availability` – Rescheduling updates slot pools safely.
15. `test_15_admin_can_view_bookings` – Admin manifest & detail inspector.
16. `test_16_admin_can_manage_slots` – Slot capacity & active toggling.
17. `test_17_admin_can_manage_holidays` – Add & delete holiday closures.
18. `test_18_excel_report_downloads_correctly` – OpenPyXL .xlsx generation.
19. `test_19_pdf_report_downloads_correctly` – ReportLab .pdf generation.
20. `test_20_unauthenticated_users_cannot_access_admin_pages` – Strict login redirect enforcement.
21. `test_21_concurrent_booking_attempts_cannot_exceed_capacity` – Multi-threaded atomic lock verification.

---

## 9. Production Linux Deployment Guide

### Systemd Gunicorn Service (`/etc/systemd/system/black_eagles.service`)
```ini
[Unit]
Description=Black Eagles Zipline Gunicorn Application Server
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/black_eagles_zipline
ExecStart=/var/www/black_eagles_zipline/venv/bin/gunicorn -c gunicorn_config.py config.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

### Static File Collection
```bash
python manage.py collectstatic --noinput
```

### Nginx & SSL Setup
Copy `nginx.conf` to `/etc/nginx/sites-available/black_eagles` and enable it:
```bash
sudo ln -s /etc/nginx/sites-available/black_eagles /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable --now black_eagles
```
Install Let's Encrypt SSL certificate:
```bash
sudo certbot --nginx -d blackeagleszipline.com -d www.blackeagleszipline.com
```

---

## 10. Commercial Handover Notice

This application was engineered by **PL SOFT TECH SOLUTIONS** to commercial production standards for **Black Eagles Zipline**.
All business details (slot timings, physical addresses, phone numbers, ticket package prices, weight and age restrictions) are fully configurable via the `/admin-panel/` console without editing source code.

#   b l a c k _ e a g l e s _ z i p l i n e  
 