# EventEase — Complete Full-Stack Event Management and Registration Platform

## 1. Project Overview

**EventEase** is a full-stack web application designed for event discovery, publishing, seat registration, venue check-in verification, and role-based administration. Built with **Python (Flask 3.x, SQLAlchemy 2.x, Flask-Security-Too)** on the backend and **Vue.js 3 (Composition API `<script setup>`, Vue Router 4, Axios, Bootstrap 5)** on the frontend, EventEase enforces strict database integrity, transactional capacity checks, and server-side token authentication.

---

## 2. Problem Statement

Organizations, universities, and technical communities frequently struggle with fragmented spreadsheets and disconnected forms when hosting conferences or workshops. Common pain points include:
- Overselling venue capacity when multiple attendees register concurrently.
- Lack of verifiable registration references for door check-ins.
- Inability to preserve historical registration records when events are cancelled.
- Weak client-side-only permission checks that expose attendee rosters to unauthorized users.

EventEase solves these problems through a relational SQLite/SQLAlchemy schema with atomic conditional capacity updates, Flask-Security-Too token authentication, and role-segmented workspaces for **Administrators**, **Event Organizers**, and **Attendees**.

---

## 3. Features

- **Authentication & User Management**:
  - Public account registration for `attendee` and `organizer` roles (public self-assignment of `admin` is strictly rejected with `403 Forbidden`).
  - Bcrypt password hashing and cryptographic token authentication via Flask-Security-Too (`Authentication-Token` header).
  - Immediate token revocation upon logout or administrator account deactivation via `fs_uniquifier` rotation.
  - Authenticated profile and password updates, plus in-app notifications.
- **Public Event Discovery**:
  - Live search by title, description, venue, or city.
  - Multi-faceted filtering by category, city, date range, pricing type (Free vs. Paid informational), and open seat availability.
  - Sorting by start date, remaining capacity, price, or title, with server-side pagination.
- **Organizer Event CRUD & Roster Management**:
  - Create, view, edit, publish, cancel, and archive events with server-side date and capacity validation.
  - Draft events with zero registrations can be permanently deleted; published events or events with registration history transition to `CANCELLED` to preserve audit records.
  - Real-time attendee roster search, status filtering, one-click or reference-code door check-in, registration cancellation, and authorized CSV export (`GET /api/events/<event_id>/registrations/export`).
- **Transactional Event Registration & Check-In**:
  - Atomic conditional SQL `UPDATE` (`registered_count < capacity`) paired with `CheckConstraint` and `UniqueConstraint` to prevent duplicate registrations and overselling under concurrent load.
  - Unique pass reference generation (`EVT-XXXX-XXXX`) and deterministic visual reference matrix on the registration confirmation pass.
- **Role-Specific Dashboards & Analytics**:
  - Live SQLAlchemy aggregations for Attendee, Organizer, and Administrator dashboards.
- **Optional Background Processing**:
  - Modular Celery and Redis task definitions (`backend/app/tasks/reminder_tasks.py`) for confirmation processing, 48-hour upcoming event reminders, and daily organizer summaries. Works seamlessly when Redis/Celery are disabled.

---

## 4. Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Backend Framework** | Python 3.10 / 3.11+, Flask 3.x |
| **ORM & Database** | Flask-SQLAlchemy 3.1+, SQLAlchemy 2.x, SQLite 3 (`PRAGMA foreign_keys=ON`) |
| **Authentication & RBAC** | Flask-Security-Too 5.x (`SQLAlchemyUserDatastore`, `Authentication-Token`, `bcrypt`) |
| **CORS & HTTP** | Flask-CORS 4.x |
| **Automated Testing** | Pytest 8+/9+ with isolated per-test SQLite database fixtures |
| **Background Jobs (Optional)** | Celery 5.x, Redis 5.x |
| **Frontend Framework** | Vue.js 3 (`<script setup>` Composition API), TypeScript |
| **Routing & HTTP** | Vue Router 4, Axios (centralized client with interceptors) |
| **Styling & Build** | Bootstrap 5.3 + Custom CSS (`src/assets/custom.css`), Vite |

---

## 5. System Architecture

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                       Vue.js 3 SPA Frontend (Vite)                      │
│  Views (16 Pages) ──► Vue Router 4 Guards ──► Centralized Axios Client  │
└──────────────────────────────────────────────────────┬──────────────────┘
                                                       │ HTTP JSON (/api/*)
                                                       │ Header: Authentication-Token
                                                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Flask 3 REST API Backend                        │
│  Flask-CORS ──► Flask-Security-Too Token & Role Decorators              │
│  Blueprints: auth, events, categories, registrations, dashboards, users │
│  Services: registration_service (Atomic Capacity Update), seed_service  │
└──────────────────────────┬───────────────────────────────────┬──────────┘
                           │ SQLAlchemy 2.x ORM                │ Optional
                           ▼                                   ▼
┌─────────────────────────────────────────┐   ┌───────────────────────────┐
│         SQLite Relational DB            │   │   Celery + Redis Worker   │
│  users, roles, roles_users, categories, │   │   Event Reminders &       │
│  events, registrations, notifications   │   │   Organizer Summaries     │
└─────────────────────────────────────────┘   └───────────────────────────┘
```

---

## 6. User Roles

1. **Administrator (`admin`)**:
   - Full oversight of platform metrics (`/api/dashboard/admin`).
   - Activate/deactivate user accounts and update user roles (`/api/users`).
   - Create, edit, and delete event categories (`/api/categories`).
   - View, edit, or cancel any event and inspect any event's attendee roster.
2. **Event Organizer (`organizer`)**:
   - Create and manage own events (`DRAFT`, `PUBLISHED`, `CANCELLED`, `ARCHIVED`).
   - View organizer analytics and per-event occupancy (`/api/dashboard/organizer`).
   - View attendee rosters for own events, check in attendees by reference code, cancel registrations, and export attendee lists to CSV.
3. **Attendee (`attendee`)**:
   - Browse and filter published events.
   - Register for eligible published events and receive a unique `EVT-XXXX-XXXX` pass reference.
   - View personal dashboard (`/api/dashboard/attendee`), registration history, and check-in pass, and cancel eligible registrations before the event ends.

---

## 7. Database Schema and Relationships

- **`roles`**:
  - `id` (PK), `name` (Unique, Indexed: `admin`, `organizer`, `attendee`), `description`.
- **`users`**:
  - `id` (PK), `email` (Unique, Indexed), `password` (bcrypt hash), `full_name`, `organization`, `phone`, `bio`, `active` (Boolean, Indexed), `fs_uniquifier` (Unique 64-char token salt), `created_at`, `updated_at`.
- **`roles_users`**:
  - Many-to-many join table linking `users.id` and `roles.id` with `UniqueConstraint(user_id, role_id)` and `ON DELETE CASCADE`.
- **`categories`**:
  - `id` (PK), `name` (Unique, Indexed), `description`, `is_active`, `created_at`.
- **`events`**:
  - `id` (PK), `title` (Indexed), `description`, `category_id` (FK -> `categories.id`, `ON DELETE RESTRICT`), `organizer_id` (FK -> `users.id`, `ON DELETE CASCADE`), `venue`, `city` (Indexed), `start_datetime` (Indexed), `end_datetime`, `registration_deadline` (Indexed), `capacity`, `registered_count`, `price`, `status` (Indexed: `DRAFT`, `PUBLISHED`, `CANCELLED`, `ARCHIVED`), `moderation_notes`, `created_at`, `updated_at`.
  - Constraints: `capacity > 0`, `registered_count >= 0 AND registered_count <= capacity`, `price >= 0`.
- **`registrations`**:
  - `id` (PK), `attendee_id` (FK -> `users.id`, `ON DELETE CASCADE`), `event_id` (FK -> `events.id`, `ON DELETE CASCADE`), `registration_reference` (Unique, Indexed), `status` (`CONFIRMED`, `CHECKED_IN`, `CANCELLED`), `notes`, `registered_at`, `checked_in_at`, `cancelled_at`.
  - Constraint: `UniqueConstraint(attendee_id, event_id, name='uq_attendee_event_registration')`.
- **`notifications`**:
  - `id` (PK), `recipient_id` (FK -> `users.id`, `ON DELETE CASCADE`), `title`, `content`, `notification_type`, `is_read`, `created_at`.

---

## 8. Repository Structure

```text
eventease/
├── backend/
│   ├── app/
│   │   ├── __init__.py              # Flask app factory, Flask-Security-Too, CORS, blueprints
│   │   ├── models/
│   │   │   ├── __init__.py          # SQLAlchemy db instance & SQLite PRAGMA foreign_keys=ON
│   │   │   ├── user.py              # User, Role, roles_users models
│   │   │   ├── category.py          # Category model
│   │   │   ├── event.py             # Event model with capacity CheckConstraints
│   │   │   ├── registration.py      # Registration model with UniqueConstraints
│   │   │   └── notification.py      # Notification model
│   │   ├── routes/
│   │   │   ├── __init__.py          # token_auth_required & roles_required_json decorators
│   │   │   ├── auth.py              # /api/auth/* endpoints
│   │   │   ├── categories.py        # /api/categories/* endpoints
│   │   │   ├── events.py            # /api/events/* endpoints
│   │   │   ├── registrations.py     # /api/registrations/*, check-in, and CSV export
│   │   │   ├── dashboards.py        # /api/dashboard/{attendee,organizer,admin}
│   │   │   └── users.py             # /api/users/* admin endpoints
│   │   ├── schemas/
│   │   │   └── validators.py        # Input, email, and ISO-8601 date validation
│   │   ├── services/
│   │   │   ├── registration_service.py # Atomic capacity updates, cancellation, check-in
│   │   │   └── seed_service.py      # Idempotent seeding of roles, categories, demo records
│   │   └── tasks/
│   │       └── reminder_tasks.py    # Optional Celery tasks & in-app reminder processors
│   ├── tests/
│   │   ├── conftest.py              # Isolated tempfile SQLite DB & auth fixtures
│   │   ├── test_auth.py
│   │   ├── test_events.py
│   │   ├── test_registrations.py
│   │   ├── test_checkin.py
│   │   └── test_admin.py
│   ├── config.py                    # Config, TestingConfig, ProductionConfig
│   ├── requirements.txt
│   └── run.py                       # Flask server entry point
├── src/
│   ├── api/
│   │   └── client.ts                # Centralized Axios client with Authentication-Token
│   ├── assets/
│   │   ├── custom.css               # Design system & responsive workspace styles
│   │   └── images/                  # Generated hero visual asset
│   ├── components/
│   │   ├── PublicNavbar.vue
│   │   ├── DashboardLayout.vue
│   │   ├── EventCard.vue
│   │   └── ConfirmModal.vue
│   ├── router/
│   │   └── index.ts                 # Vue Router 4 configuration (16 views)
│   ├── stores/
│   │   └── auth.ts                  # Reactive auth & toast store
│   ├── views/                       # All 16 application pages
│   ├── App.vue
│   └── main.ts
├── .env.example
├── .gitignore
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

---

## 9. Prerequisites

- **Python**: 3.10 or 3.11+
- **Node.js**: 18.x or 20.x+ with `npm`
- **SQLite 3**: Included in the Python standard library (`sqlite3`)
- **Redis** *(Optional)*: Only required if running background Celery workers with `CELERY_ENABLED=true`

---

## 10. Backend Installation

```bash
# Create and activate a Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt
```

---

## 11. Frontend Installation

```bash
npm install
```

---

## 12. Environment Configuration

Copy `.env.example` to `.env` if customizing ports or secrets:

```bash
cp .env.example .env
```

Key variables in `.env.example`:
- `VITE_API_BASE_URL="/api"` (proxied to `http://127.0.0.1:5000` in development via `vite.config.ts`, or set to `http://localhost:5000/api` if running standalone)
- `FLASK_PORT="5000"`
- `SECRET_KEY` and `SECURITY_PASSWORD_SALT`
- `DATABASE_URL="sqlite:///backend/eventease.db"`
- `CELERY_ENABLED="false"`

---

## 13. Database Initialization

When `create_app()` in `backend/app/__init__.py` starts, it automatically runs `db.create_all()` and executes `seed_initial_data()` idempotently. This guarantees that:
1. Default roles (`admin`, `organizer`, `attendee`) exist.
2. Default categories (`Technology`, `Education`, `Business`, `Music and Entertainment`, `Sports`, `Workshops`, `Community`) exist.
3. Demo accounts and sample events are seeded on first run without duplicating records on subsequent restarts.

---

## 14. Commands to Run the Application

### Option A: Unified Development Command (Recommended)
`vite.config.ts` includes an automatic launcher plugin that starts the Flask backend on port `5000` (if not already listening) and serves the Vue 3 application on port `3000` with `/api` proxying:

```bash
npm run dev
```

### Option B: Run Backend and Frontend Separately

Terminal 1 (Flask Backend on port 5000):
```bash
.venv/bin/python backend/run.py
```

Terminal 2 (Vite Frontend on port 3000):
```bash
npm run dev
```

### Production Frontend Build Verification
```bash
npm run build
```

---

## 15. Demo Account Setup

The database seeder (`backend/app/services/seed_service.py`) creates the following ready-to-use accounts (also accessible via one-click buttons on the `/login` page):

| Role | Email | Password |
| :--- | :--- | :--- |
| **Administrator** | `admin@eventease.io` | `AdminPassword123!` |
| **Event Organizer 1** | `organizer@eventease.io` | `OrganizerPassword123!` |
| **Event Organizer 2** | `organizer2@eventease.io` | `OrganizerPassword123!` |
| **Attendee 1** | `attendee@eventease.io` | `AttendeePassword123!` |
| **Attendee 2** | `attendee2@eventease.io` | `AttendeePassword123!` |

---

## 16. Actual API Documentation

All endpoints are prefixed with `/api` and return JSON responses (except `/api/events/<event_id>/registrations/export`, which returns `text/csv`).

### Authentication (`/api/auth`)
- `POST /api/auth/register` — Public registration for `attendee` or `organizer`. Returns `201 Created` with `token` and `user`.
- `POST /api/auth/login` — Authenticates credentials and returns `200 OK` with Flask-Security-Too `token` and `user`.
- `GET /api/auth/me` — Returns current authenticated user profile (`Authentication-Token` required).
- `PUT /api/auth/profile` — Updates full name, organization, phone, bio, or password (`Authentication-Token` required).
- `POST /api/auth/logout` — Rotates `fs_uniquifier` to invalidate current token (`Authentication-Token` required).
- `GET /api/auth/notifications` — Lists recent in-app notifications for the user.
- `PUT /api/auth/notifications/<notification_id>/read` — Marks a notification as read.

### Categories (`/api/categories`)
- `GET /api/categories` — Lists categories (`?include_counts=true&active_only=true`).
- `POST /api/categories` — Creates a category (`admin` only).
- `PUT /api/categories/<category_id>` — Updates a category (`admin` only).
- `DELETE /api/categories/<category_id>` — Deletes an unused category (`admin` only; returns `409 Conflict` if events reference it).

### Events (`/api/events`)
- `GET /api/events` — Lists events with query filters: `search`, `category_id`, `city`, `start_date`, `end_date`, `price_type` (`free`|`paid`), `availability` (`open`), `status`, `mine` (`true`), `sort_by`, `page`, `page_size`.
- `GET /api/events/<event_id>` — Retrieves event details, stats (if owner/admin), and `my_registration` (if authenticated).
- `POST /api/events` — Creates an event (`organizer` or `admin`).
- `PUT /api/events/<event_id>` — Updates an event (creator `organizer` or `admin`).
- `DELETE /api/events/<event_id>` — Permanently deletes a `DRAFT` event with 0 registrations (`action: "DELETED"`), or transitions a published/populated event to `CANCELLED` (`action: "CANCELLED"`) to preserve registration history.

### Registrations & Check-In (`/api`)
- `POST /api/events/<event_id>/registrations` — Registers the authenticated user for a published event (`201 Created` or `409 Conflict`).
- `GET /api/registrations/me` — Lists the authenticated user's registrations (`?status=ALL|CONFIRMED|CHECKED_IN|CANCELLED`).
- `GET /api/events/<event_id>/registrations` — Lists attendee registrations and summary counts for an event (event's `organizer` or `admin`).
- `GET /api/events/<event_id>/registrations/export` — Downloads a `text/csv` attendee roster (event's `organizer` or `admin`).
- `GET /api/registrations/<registration_id>` — Retrieves registration pass details (registration owner, event organizer, or admin).
- `POST /api/registrations/<registration_id>/cancel` — Cancels a registration and atomically increments remaining capacity.
- `POST /api/registrations/<registration_id>/check-in` — Checks in an attendee by registration ID (event's `organizer` or `admin`).
- `POST /api/events/<event_id>/check-in` — Checks in an attendee by `{"registration_reference": "EVT-XXXX-XXXX"}` (event's `organizer` or `admin`).

### Dashboards (`/api/dashboard`)
- `GET /api/dashboard/attendee` — Upcoming, past, checked-in, and cancelled registration metrics for the current user.
- `GET /api/dashboard/organizer` — Total events, published/draft/cancelled counts, active registrations, remaining capacity, and per-event occupancy breakdown.
- `GET /api/dashboard/admin` — Platform-wide user, event, and registration counts, category group-by breakdown, and recent activity feed (`admin` only).

### User Administration (`/api/users`)
- `GET /api/users` — Lists users with `search`, `role`, and `active` filters (`admin` only).
- `PUT /api/users/<user_id>/status` — Activates or deactivates a user (`{"active": false}`) and rotates `fs_uniquifier` (`admin` only).
- `PUT /api/users/<user_id>/role` — Assigns role (`attendee`, `organizer`, `admin`) to a user (`admin` only).

---

## 17. Authentication Examples

Flask-Security-Too expects the token in the `Authentication-Token` HTTP header:

```bash
# 1. Log in and obtain token
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "organizer@eventease.io", "password": "OrganizerPassword123!"}'

# 2. Call a protected endpoint using Authentication-Token
curl -X GET http://localhost:5000/api/auth/me \
  -H "Authentication-Token: <YOUR_TOKEN_HERE>"
```

---

## 18. Request and Response Examples

### Create Event (`POST /api/events`)
Request:
```json
{
  "title": "Systems Engineering Colloquium",
  "description": "Deep dive into storage engines and distributed consensus.",
  "category_id": 1,
  "venue": "Forum Hall 2B",
  "city": "San Francisco",
  "start_datetime": "2026-11-15T09:00:00",
  "end_datetime": "2026-11-15T17:00:00",
  "registration_deadline": "2026-11-12T18:00:00",
  "capacity": 100,
  "price": 0.0,
  "status": "PUBLISHED"
}
```

Response (`201 Created`):
```json
{
  "message": "Event created successfully.",
  "event": {
    "id": 10,
    "title": "Systems Engineering Colloquium",
    "category_id": 1,
    "category_name": "Technology",
    "venue": "Forum Hall 2B",
    "city": "San Francisco",
    "capacity": 100,
    "registered_count": 0,
    "remaining_capacity": 100,
    "price": 0.0,
    "is_free": true,
    "status": "PUBLISHED",
    "is_registration_open": true
  }
}
```

### Register for Event (`POST /api/events/10/registrations`)
Response (`201 Created`):
```json
{
  "message": "Registration confirmed.",
  "registration": {
    "id": 7,
    "attendee_id": 4,
    "event_id": 10,
    "registration_reference": "EVT-8K2M-9P4Q",
    "status": "CONFIRMED",
    "registered_at": "2026-10-13T15:20:00"
  }
}
```

---

## 19. CRUD Workflow Descriptions

1. **Event Lifecycle**: Organizers create an event in `DRAFT` or `PUBLISHED` status. Dates are validated so `registration_deadline <= start_datetime < end_datetime`. Capacity cannot be reduced below `registered_count`. Deleting a `DRAFT` event with no registrations removes the row; deleting a `PUBLISHED` event or an event with registrations transitions its status to `CANCELLED` so attendee registration records remain intact.
2. **Registration & Capacity Lifecycle**: When an attendee registers, `register_attendee_for_event()` executes an atomic conditional `UPDATE events SET registered_count = registered_count + 1 WHERE id = :id AND status = 'PUBLISHED' AND registered_count < capacity`. If `rowcount == 0`, the transaction rolls back and returns `409 Conflict`. Cancelling a registration decrements `registered_count` atomically and sets `status = 'CANCELLED'`.
3. **Check-In Lifecycle**: Organizers can check in a `CONFIRMED` registration once via button click or reference lookup. The backend sets `status = 'CHECKED_IN'` and records `checked_in_at`. Duplicate check-ins return `409 Conflict`, and cancelled registrations return `400 Bad Request`.

---

## 20. Automated Testing Instructions

Run the complete backend Pytest suite (23 automated tests covering authentication, role restrictions, event CRUD, registration constraints, multi-threaded concurrency on the last available seat, check-in validation, and admin operations) against an isolated temporary SQLite database:

```bash
.venv/bin/pytest backend/tests -v
```

---

## 21. Optional Celery and Redis Setup

EventEase works out of the box without Redis or Celery. To enable optional background task queuing:
1. Start a local Redis server on `redis://localhost:6379/0`.
2. Set `CELERY_ENABLED="true"` in `.env`.
3. Start the Celery worker:
```bash
.venv/bin/celery -A backend.app.tasks.reminder_tasks.celery_app worker --loglevel=info
```

---

## 22. Troubleshooting

- **`401 Unauthorized` on API calls**: Verify that the `Authentication-Token` header is present and that the user account has not been deactivated or logged out.
- **Port 5000 or 3000 already in use**: Check running processes or adjust `FLASK_PORT` in `.env`.
- **SQLite database reset**: Delete `backend/eventease.db` and restart the backend to re-seed fresh demo data.

---

## 23. Screenshots Section

When running locally (`http://localhost:3000`), you can capture screenshots of:
- Landing Page (`/`): Editorial hero banner, live platform KPIs, featured upcoming events, and category directory.
- Event Discovery (`/events`): Multi-filter search bar and real-time seat availability cards.
- Organizer Console (`/organizer/dashboard`, `/organizer/events`, `/organizer/events/1/attendees`): Occupancy table, express reference check-in bar, and CSV export.
- Attendee Portal (`/attendee/dashboard`, `/registrations/1`): Digital pass with `EVT-XXXX-XXXX` reference and deterministic check-in code.
- Admin Governance (`/admin/dashboard`, `/admin/users`, `/admin/categories`): Category distribution, role selector, and account activation controls.

---

## 24. Known Limitations and Future Enhancements

- **SQLite Concurrency Model**: SQLite serializes write transactions at the database file level (`timeout=15`), which safely enforces our atomic `UPDATE ... WHERE registered_count < capacity` check for single-node deployments. High-throughput multi-node deployments should point `DATABASE_URL` to PostgreSQL.
- **Informational Event Pricing**: Paid event prices are clearly labeled as informational (`No Online Payment`) because no third-party payment gateway (e.g., Stripe) is configured.
- **In-App Notifications**: Notifications are persisted in the `notifications` table and displayed in the user's profile workspace; external SMTP email delivery is intentionally omitted unless an email provider is configured.
