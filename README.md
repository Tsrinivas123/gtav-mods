# PawanMod - GTA V Mods Marketplace 🚗⚡

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-Django--5.0-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-26%2F26%20passing-brightgreen.svg)]()

A high-performance, modern digital marketplace web application designed for GTA V vehicle models, scripts, graphics presets, maps, character skins, and interiors. Features a sleek cyberpunk visual identity, accessible mobile-first responsive design, integrated multi-gateway payments, instant download delivery, and a custom administrative dashboard.

---

## 🌟 Key Features

### 🛍️ Storefront & E-Commerce
- **Mod Catalogue & Filtering**: Browse mods by category (Vehicles, Weapons, Scripts, Maps, Skins, Presets) with live price sliders, availability status toggles, and mobile filter drawers.
- **Search & Layout Toggle**: Instant search across mod names, tags, and descriptions with persistence for Grid/List view preference.
- **Product Details & Media**: High-res image carousel, specifications tab navigation (About, Requirements, Installation Guide, Version History), and social sharing capabilities.
- **Shopping Cart & Coupons**: Dynamic AJAX cart management, automatic discount calculations, and promo code support (e.g. `SAVE20`, `WELCOME10`).
- **Seamless Checkout & Payments**: Multi-gateway payment support including UPI QR Code modal simulation, Razorpay Card processing, and PayPal integration.

### 👤 User Account Dashboard
- **Profile Management**: Update billing address, avatar images, and account details.
- **My Purchased Downloads**: One-click instant digital download unlocking for purchased mods with version tracking.
- **Order History & Invoices**: Generate and view PDF invoices for completed transactions.
- **Wishlist**: Quick-save favorite mods across storefront cards.

### 🛠️ Custom Admin Panel (`/custom-admin/`)
- **Dashboard Analytics**: Real-time sales statistics, revenue summaries, pending order flags, category breakdowns, and user activity metrics.
- **Product Inventory Management**: Full CRUD operations for mods, rich text installation guides, pricing, discount math, and versioning.
- **Media Manager**: Dedicated upload and reordering workflows for primary thumbnails, screenshots gallery, and secure downloadable zip archives.
- **Category & Coupon Control**: Safe category deletion with product reassignment rules, coupon expiration trackers, and bulk product actions.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.11+, Django 5.0 framework
- **Frontend**: HTML5, Vanilla CSS3 (Custom Design System with CSS Variables, Dark Glassmorphism, and Cyberpunk Accents `#ff6b00`), Modern ES6+ JavaScript
- **Database**: SQLite (Development) / PostgreSQL compatible
- **Static Assets**: WhiteNoise, FontAwesome 6 Pro icons, Google Fonts (Inter & Orbitron)
- **Package Management**: `uv` / `pip`

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.11+ installed
- `uv` installed (`pip install uv` or `curl -sSf https://astral.sh/uv/install.sh | sh`)

### 1. Clone the Repository
```bash
git clone https://github.com/Tsrinivas123/gtav-mods.git
cd gtav-mods
```

### 2. Set Up Virtual Environment & Dependencies
```bash
# Using uv (recommended)
uv venv
uv pip install -r requirements.txt
```

### 3. Run Database Migrations & Seed Sample Data
```bash
uv run python manage.py migrate
uv run python manage.py seed
```

### 4. Start the Development Server
```bash
uv run python manage.py runserver 8000
```
Open **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** in your browser to view the application!

---

## 🔐 Administrative Access

- **Custom Admin Portal**: [http://127.0.0.1:8000/custom-admin/](http://127.0.0.1:8000/custom-admin/)
- **Standard Django Admin**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

### Default Admin Credentials
- **Username**: `admin`
- **Password**: `admin123`

---

## 🧪 Running Automated Tests

Run the complete test suite (26 unit and integration test cases covering marketplace logic, authentication, cart/checkout flows, and admin CRUD actions):

```bash
uv run python manage.py test
```

Run Django system diagnostic checks:
```bash
uv run python manage.py check
```

---

## 📁 Directory Structure

```text
pawanmod/
├── accounts/               # User authentication, profiles, & wishlist views
├── blog/                   # Blog posts, reading time, & news views
├── core/                   # Project configuration, custom admin views & forms
│   ├── admin_views.py      # Custom admin portal views & dashboard logic
│   ├── admin_forms.py      # Custom admin forms & validations
│   └── settings.py         # Django settings configuration
├── marketplace/            # Storefront, product catalogue, categories, & views
├── orders/                 # Shopping cart, checkout, payment gateways, & invoices
├── static/                 # CSS design system, JavaScript modules, & branding
│   ├── css/style.css       # Core design system stylesheet
│   └── js/                 # main.js (Toast & Canvas), store.js, cart.js
├── templates/              # HTML5 templates & admin_custom layouts
└── manage.py               # Django CLI utility
```

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
