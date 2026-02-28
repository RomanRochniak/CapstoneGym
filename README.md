# CapstoneGym — RoshaClub (Gym Membership Management System)

**Demo demo:** https://capstonegym.onrender.com

RoshaClub is a Django web application for gym membership management with a modern, product-like UI and an **AI Fitness Assistant**.  
Users can browse training programs, view trainer profiles, purchase memberships securely via Stripe, manage their profiles, and interact in a community feed.

---

## Table of Contents
- [What the app does](#what-the-app-does)
- [Main Features](#main-features)
- [AI Fitness Assistant](#ai-fitness-assistant)
- [UI and UX](#ui-and-ux)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation and Setup](#installation-and-setup)
- [Environment Variables](#environment-variables)
- [Database](#database)
- [Run the App](#run-the-app)
- [Stripe Payments](#stripe-payments)
- [Community Feed (AJAX)](#community-feed-ajax)
- [Admin Panel](#admin-panel)
- [Core Models](#core-models)
- [Key Routes](#key-routes)
- [Security Notes](#security-notes)
- [Contact](#contact)

---

## What the app does

RoshaClub is built around a realistic gym workflow:

1. A user creates an account and logs in.
2. They browse training programs and trainer profiles.
3. They purchase a membership for a chosen program using Stripe.
4. Their profile shows membership status and expiration.
5. They can post updates in a community feed and interact with other members.
6. They can ask the AI assistant for program recommendations and guidance based on the site context.

---

## Main Features

### Authentication
- User registration and login/logout
- Session-based authentication (Django auth)

### Programs and Trainers
- Browse training programs (with price, description, duration)
- Trainer profiles with specialization + details + photos
- Program-to-trainer relationship

### Membership Management
- Purchase membership tied to a program
- Membership has `start_date`, `end_date`, and `status`
- Clear visibility in profile: active/expired/pending and expiration date

### Payments
- Stripe integration (card payments)
- Google Pay support through Stripe flow
- Payment success/failure feedback page

### Community Feed
- Create posts (text + optional image URL)
- Like/unlike posts
- Edit/delete own posts
- AJAX interactions for smooth UX (no full page refresh for likes/edits)

### Responsive UI
- Layout designed to work across desktop/tablet/mobile
- Card-based UI for programs/trainers
- Consistent navigation + section spacing + typography hierarchy

---

## AI Fitness Assistant

The AI assistant is an integrated feature that behaves like an “in-app coach”.

### What it does
- Provides fitness guidance and program recommendations
- Uses contextual information (programs, trainers, membership-related info) to reduce hallucinations
- Stores conversation sessions and message history in the database

### Providers supported
You can run the assistant with either:
- **Ollama** (local model for development)
- **Gemini** (cloud model; requires API key)

Switching providers is done via environment variables (see [Environment Variables](#environment-variables)).

### API Endpoint
**`POST /api/ai/chat/`**

- Requires authentication (user must be logged in)
- Payload:
  - `message` (string): user prompt
  - optionally may support `session_id` depending on your implementation
- Response includes:
  - `session_id`
  - `response` (assistant message)
  - provider/model metadata

Example:
```bash
curl -X POST http://127.0.0.1:8000/api/ai/chat/   -H "Content-Type: application/json"   -d '{"message":"I want to gain muscle. Which program should I choose?"}'
```

### Controls (stability + cost)
The assistant includes runtime controls:
- **Rate limiting** (requests per user per minute)
- **Short-term caching** (avoid repeated calls for the same prompt)
- **Timeout** (avoid hanging external calls)

Configured via:
- `AI_RATE_LIMIT_PER_MIN`
- `AI_CACHE_SECONDS`
- `AI_TIMEOUT_SECONDS`

---

## UI and UX

This project is intentionally built to look and feel like a product, not a basic CRUD demo.

Highlights:
- Consistent base layout (`layout.html`) across pages
- Card UI for trainers/programs with hover feedback
- Clear CTAs for membership purchase flow
- Community feed interactions designed to feel instant (AJAX)
- Smooth animations (Intersection Observer) where applicable

---

## Tech Stack

- **Backend**: Python, Django
- **Frontend**: Django templates, HTML, CSS, JavaScript
- **Database**: SQLite (default dev) or PostgreSQL (optional)
- **Payments**: Stripe (cards + Google Pay)
- **AI**: Ollama (local) / Gemini (cloud)

---

## Project Structure

(High-level; exact names may differ depending on your current repo.)

- `capstone/` — Django project config (settings, urls)
- `gym/` / `gym_app/` — main app (programs, trainers, membership, payments, community)
- `ai_assistant/` — AI assistant app (chat sessions/messages + API endpoint)
- `services/` — AI provider clients and context builder utilities
- `templates/` — Django templates
- `static/` — CSS/JS/assets
- `media/` — uploaded images

---

## Installation and Setup

### Prerequisites
- Python 3.x
- pip
- Django 4.x (installed via requirements)
- Stripe test keys (for local testing)
- Optional:
  - PostgreSQL
  - Ollama (if using local AI)
  - Gemini API key (if using Gemini)

### 1) Clone
```bash
git clone https://github.com/RomanRochniak/CapstoneGym.git
cd CapstoneGym
```

### 2) Create and activate venv
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
# source .venv/bin/activate
```

### 3) Install dependencies
```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file in the project root.

Example template:
```env
# Django
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=1
ALLOWED_HOSTS=127.0.0.1,localhost

# Stripe
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...

# Optional: Stripe webhook signature (if used)
# STRIPE_WEBHOOK_SECRET=whsec_...

# AI provider: ollama | gemini
AI_PROVIDER=ollama

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# Gemini
GEMINI_API_KEY=
GEMINI_MODEL=gemini-1.5-flash

# AI runtime controls
AI_RATE_LIMIT_PER_MIN=12
AI_CACHE_SECONDS=120
AI_TIMEOUT_SECONDS=12
```

---

## Database

### SQLite (default)
No setup required. Django creates `db.sqlite3` automatically after migrations.

### PostgreSQL (optional)
1) Create DB and user:
```bash
createdb roshaclub_db
createuser roshaclub_user
psql -d roshaclub_db -c "GRANT ALL PRIVILEGES ON DATABASE roshaclub_db TO roshaclub_user;"
```

2) Configure in `settings.py`:
```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "roshaclub_db",
        "USER": "roshaclub_user",
        "PASSWORD": "YOUR_PASSWORD",
        "HOST": "localhost",
        "PORT": "5432",
    }
}
```

---

## Run the App

### 1) Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 2) Create admin
```bash
python manage.py createsuperuser
```

### 3) Start server
```bash
python manage.py runserver
```

Open:
- App: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

---

## Stripe Payments

### Test cards
| Card Number            | Card Type   | Result                    |
|------------------------|-------------|---------------------------|
| 4242 4242 4242 4242    | Visa        | Successful payment        |
| 4000 0000 0000 0002    | Visa        | Payment declined          |
| 5555 5555 5555 4444    | Mastercard  | Successful payment        |

### How payment works (logic overview)
1. User selects a training program.
2. The payment page collects payment information (card or Google Pay).
3. Stripe charge / payment intent is created.
4. After success:
   - a `Membership` record is created/updated
   - user is redirected to a result page (`success`)

### Webhook (if enabled)
Endpoint:
- `POST /webhook/`

Note: webhook signature verification is the correct approach if you rely on webhooks in production.

---

## Community Feed (AJAX)

The community feed supports interactive actions without full page reload.

### Frontend behavior
- Like/unlike sends POST requests via fetch
- Edit post sends JSON to backend and updates DOM on success
- CSRF token is included in AJAX requests

### Backend behavior
- Like add/remove endpoints update M2M relation (`Post.likes`)
- Edit endpoint validates ownership before updating
- Delete endpoint blocks users from deleting others’ posts

---

## Admin Panel

Admin URL:
- http://127.0.0.1:8000/admin/

Use admin to manage:
- Trainers
- Training programs
- Memberships
- Posts/payments data (depending on registered models)

---

## Core Models

(Conceptual overview; field names may vary slightly.)

### Trainer
- `name`
- `specialization`
- `description`
- `photo`

### TrainingProgram
- `name`
- `description`
- `duration`
- `price`
- `trainer` (FK)

### Membership
- `user` (FK)
- `program` (FK)
- `start_date`
- `end_date`
- `status` (`active` / `expired` / `pending`)

### Payment
- `stripe_charge_id`
- `amount`
- `created`

### Post
- `user` (FK)
- `content`
- `image_url` (optional)
- `created_at`
- `likes` (M2M)

---

## Key Routes

(Exact routes depend on your URL config; these are the main ones referenced in the project.)

- Programs:
  - `/training-programs/`
- Payments:
  - `/payments/?program_id=<id>`
  - `/success/<status>/<message>/<program_id>/`
- Community:
  - `/community/` (or `/gym/community/` depending on routing)
- AI:
  - `/api/ai/chat/`
- Admin:
  - `/admin/`
- Stripe webhook (if present):
  - `/webhook/`

---

## Security Notes

- CSRF protection should remain enabled for form submissions and AJAX POSTs.
- Do not commit `.env` files or secret keys to the repository.
- Stripe secret keys and AI API keys must be stored as environment variables.

---

## Contact

For questions or feedback: **rochnyak180405@gmail.com** (Roman Rochniak)
