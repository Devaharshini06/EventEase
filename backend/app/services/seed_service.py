from datetime import datetime, timedelta, timezone
from flask_security.utils import hash_password
from ..models import db, User, Role, Category, Event, Registration, Notification

DEFAULT_ROLES = [
    ("admin", "Platform Administrator with full user, category, and event oversight."),
    ("organizer", "Event Organizer authorized to create, publish, and manage events and check-ins."),
    ("attendee", "Event Attendee authorized to discover events and manage personal registrations."),
]

DEFAULT_CATEGORIES = [
    ("Technology", "Software engineering, cloud architecture, AI systems, and developer summits."),
    ("Education", "Academic symposiums, research colloquia, and curriculum innovation forums."),
    ("Business", "Executive leadership, venture strategy, product management, and operations."),
    ("Music and Entertainment", "Live acoustic sessions, film screenings, and cultural showcases."),
    ("Sports", "Endurance races, athletic clinics, and competitive sports tournaments."),
    ("Workshops", "Hands-on technical bootcamps, design studios, and craft intensives."),
    ("Community", "Civic meetups, sustainability drives, and open-source contributor gatherings."),
]


def seed_initial_data(user_datastore, seed_demo_records: bool = True):
    """
    Idempotently seeds required roles, default categories, and demo accounts/events.
    """
    for role_name, role_desc in DEFAULT_ROLES:
        user_datastore.find_or_create_role(name=role_name, description=role_desc)
    db.session.commit()

    category_map = {}
    for cat_name, cat_desc in DEFAULT_CATEGORIES:
        cat = Category.query.filter_by(name=cat_name).first()
        if not cat:
            cat = Category(name=cat_name, description=cat_desc, is_active=True)
            db.session.add(cat)
            db.session.flush()
        category_map[cat_name] = cat
    db.session.commit()

    if not seed_demo_records:
        return

    # Seed Demo Users idempotently
    demo_users = [
        {
            "email": "admin@eventease.io",
            "password": "AdminPassword123!",
            "full_name": "Elena Rostova",
            "organization": "EventEase Platform Operations",
            "phone": "+1 (415) 890-4100",
            "bio": "Director of Platform Trust & Operations at EventEase.",
            "role": "admin",
        },
        {
            "email": "organizer@eventease.io",
            "password": "OrganizerPassword123!",
            "full_name": "Marcus Vance",
            "organization": "Vance Systems & Architecture Guild",
            "phone": "+1 (206) 555-0194",
            "bio": "Principal Conference Producer organizing distributed systems and design engineering forums.",
            "role": "organizer",
        },
        {
            "email": "organizer2@eventease.io",
            "password": "OrganizerPassword123!",
            "full_name": "Priya Nair",
            "organization": "Meridian Design & Civic Labs",
            "phone": "+1 (646) 555-0148",
            "bio": "Curator of hands-on workshops, civic technology sprints, and design leadership retreats.",
            "role": "organizer",
        },
        {
            "email": "attendee@eventease.io",
            "password": "AttendeePassword123!",
            "full_name": "Sophia Chen",
            "organization": "Apex Cloud Infrastructure",
            "phone": "+1 (650) 555-0182",
            "bio": "Staff Systems Engineer passionate about distributed databases and technical workshops.",
            "role": "attendee",
        },
        {
            "email": "attendee2@eventease.io",
            "password": "AttendeePassword123!",
            "full_name": "Liam O'Connor",
            "organization": "Northstar Analytics",
            "phone": "+1 (312) 555-0175",
            "bio": "Product analyst and community event participant.",
            "role": "attendee",
        },
    ]

    created_users = {}
    for u_info in demo_users:
        user = User.query.filter_by(email=u_info["email"]).first()
        if not user:
            user = user_datastore.create_user(
                email=u_info["email"],
                password=hash_password(u_info["password"]),
                full_name=u_info["full_name"],
                organization=u_info["organization"],
                phone=u_info["phone"],
                bio=u_info["bio"],
                active=True,
            )
            role_obj = Role.query.filter_by(name=u_info["role"]).first()
            if role_obj:
                user_datastore.add_role_to_user(user, role_obj)
            db.session.flush()
        created_users[u_info["email"]] = user
    db.session.commit()

    # Seed Demo Events if none exist yet
    if Event.query.count() == 0:
        now = datetime.now(timezone.utc).replace(tzinfo=None).replace(minute=0, second=0, microsecond=0)
        org1 = created_users["organizer@eventease.io"]
        org2 = created_users["organizer2@eventease.io"]
        att1 = created_users["attendee@eventease.io"]
        att2 = created_users["attendee2@eventease.io"]

        sample_events = [
            {
                "title": "Distributed Systems & Storage Architecture Summit",
                "description": (
                    "An intensive full-day engineering symposium exploring consensus protocols, "
                    "zero-downtime schema migrations, SQLite/PostgreSQL transactional guarantees, "
                    "and production observability at scale. Includes keynote talks and architecture reviews."
                ),
                "category": category_map["Technology"],
                "organizer": org1,
                "venue": "Yerba Buena Center for the Arts, Forum Hall",
                "city": "San Francisco",
                "start_datetime": now + timedelta(days=14, hours=9),
                "end_datetime": now + timedelta(days=14, hours=17),
                "registration_deadline": now + timedelta(days=12, hours=18),
                "capacity": 120,
                "price": 0.0,
                "status": "PUBLISHED",
            },
            {
                "title": "Applied Interface Systems & Design Engineering Workshop",
                "description": (
                    "Hands-on studio workshop focused on high-density operational tables, typography scales, "
                    "accessible keyboard navigation, and zero-latency state management in modern web applications."
                ),
                "category": category_map["Workshops"],
                "organizer": org2,
                "venue": "Cooper Hewitt Design Annex, Studio B",
                "city": "New York",
                "start_datetime": now + timedelta(days=21, hours=10),
                "end_datetime": now + timedelta(days=21, hours=16),
                "registration_deadline": now + timedelta(days=19, hours=23),
                "capacity": 45,
                "price": 85.0,
                "status": "PUBLISHED",
            },
            {
                "title": "Enterprise Product Leadership & Operations Forum",
                "description": (
                    "Executive roundtable and case-study sessions examining B2B SaaS growth metrics, "
                    "cross-functional engineering alignment, and sustainable operational cadences."
                ),
                "category": category_map["Business"],
                "organizer": org1,
                "venue": "Merchandise Mart Conference Suite 400",
                "city": "Chicago",
                "start_datetime": now + timedelta(days=30, hours=9),
                "end_datetime": now + timedelta(days=30, hours=18),
                "registration_deadline": now + timedelta(days=27, hours=17),
                "capacity": 80,
                "price": 150.0,
                "status": "PUBLISHED",
            },
            {
                "title": "Open Source Maintainers & Civic Data Colloquium",
                "description": (
                    "Community-driven gathering connecting municipal open-data engineers, university researchers, "
                    "and open-source maintainers building public digital infrastructure."
                ),
                "category": category_map["Community"],
                "organizer": org2,
                "venue": "Seattle Central Library, Level 4 Auditorium",
                "city": "Seattle",
                "start_datetime": now + timedelta(days=10, hours=13),
                "end_datetime": now + timedelta(days=10, hours=18),
                "registration_deadline": now + timedelta(days=9, hours=12),
                "capacity": 90,
                "price": 0.0,
                "status": "PUBLISHED",
            },
            {
                "title": "University Computer Science Pedagogy & Lab Symposium",
                "description": (
                    "Academic colloquium on automated grading pipelines, full-stack capstone design, "
                    "and reproducible software testing environments for undergraduate curricula."
                ),
                "category": category_map["Education"],
                "organizer": org1,
                "venue": "MIT Stata Center, Kirsch Auditorium",
                "city": "Boston",
                "start_datetime": now + timedelta(days=40, hours=9),
                "end_datetime": now + timedelta(days=40, hours=16),
                "registration_deadline": now + timedelta(days=36, hours=17),
                "capacity": 150,
                "price": 0.0,
                "status": "PUBLISHED",
            },
            {
                "title": "Acoustic Chamber & Modular Synthesis Evening",
                "description": (
                    "An evening performance and technical talk exploring live acoustic instrumentation "
                    "paired with custom analog modular synthesizers and spatial audio routing."
                ),
                "category": category_map["Music and Entertainment"],
                "organizer": org2,
                "venue": "Paramount Theatre Studio Lounge",
                "city": "Austin",
                "start_datetime": now + timedelta(days=18, hours=19),
                "end_datetime": now + timedelta(days=18, hours=22),
                "registration_deadline": now + timedelta(days=17, hours=18),
                "capacity": 60,
                "price": 35.0,
                "status": "PUBLISHED",
            },
            {
                "title": "Bayfront Half-Marathon & Endurance Biomechanics Clinic",
                "description": (
                    "Timed 10K/21K waterfront run preceded by a sports science clinic on VO2 max pacing, "
                    "hydration strategy, and injury prevention."
                ),
                "category": category_map["Sports"],
                "organizer": org1,
                "venue": "Crissy Field East Beach Pavilion",
                "city": "San Francisco",
                "start_datetime": now + timedelta(days=25, hours=7),
                "end_datetime": now + timedelta(days=25, hours=13),
                "registration_deadline": now + timedelta(days=22, hours=20),
                "capacity": 200,
                "price": 45.0,
                "status": "PUBLISHED",
            },
            {
                "title": "Zero-Trust Security Architecture Review (Draft)",
                "description": (
                    "Upcoming technical working session on hardware security modules, mTLS service meshes, "
                    "and role-based access auditing. Currently in organizer draft mode."
                ),
                "category": category_map["Technology"],
                "organizer": org1,
                "venue": "Moscone West Room 2014",
                "city": "San Francisco",
                "start_datetime": now + timedelta(days=50, hours=10),
                "end_datetime": now + timedelta(days=50, hours=15),
                "registration_deadline": now + timedelta(days=45, hours=17),
                "capacity": 50,
                "price": 0.0,
                "status": "DRAFT",
            },
            {
                "title": "Spring Systems Reliability Retrospective",
                "description": (
                    "Completed engineering retrospective covering incident response playbooks, "
                    "chaos testing lessons, and database failover drills."
                ),
                "category": category_map["Technology"],
                "organizer": org1,
                "venue": "Bell Harbor International Conference Center",
                "city": "Seattle",
                "start_datetime": now - timedelta(days=15, hours=8),
                "end_datetime": now - timedelta(days=15, hours=2),
                "registration_deadline": now - timedelta(days=18),
                "capacity": 75,
                "price": 0.0,
                "status": "PUBLISHED",
            },
        ]

        created_events = []
        for ev_data in sample_events:
            ev = Event(
                title=ev_data["title"],
                description=ev_data["description"],
                category_id=ev_data["category"].id,
                organizer_id=ev_data["organizer"].id,
                venue=ev_data["venue"],
                city=ev_data["city"],
                start_datetime=ev_data["start_datetime"],
                end_datetime=ev_data["end_datetime"],
                registration_deadline=ev_data["registration_deadline"],
                capacity=ev_data["capacity"],
                registered_count=0,
                price=ev_data["price"],
                status=ev_data["status"],
            )
            db.session.add(ev)
            db.session.flush()
            created_events.append(ev)

        # Seed initial registrations with accurate registered_count
        reg_specs = [
            (att1, created_events[0], "CONFIRMED", "EVT-A101-SF99", None),
            (att2, created_events[0], "CHECKED_IN", "EVT-A102-SF88", now - timedelta(hours=1)),
            (att1, created_events[1], "CONFIRMED", "EVT-B201-NY77", None),
            (att1, created_events[3], "CONFIRMED", "EVT-C301-SE66", None),
            (att2, created_events[2], "CONFIRMED", "EVT-D401-CH55", None),
            (att1, created_events[8], "CHECKED_IN", "EVT-P901-SE11", now - timedelta(days=15, hours=7)),
        ]
        for attendee, ev, status_val, ref_code, checked_dt in reg_specs:
            reg = Registration(
                attendee_id=attendee.id,
                event_id=ev.id,
                registration_reference=ref_code,
                status=status_val,
                registered_at=now - timedelta(days=3),
                checked_in_at=checked_dt,
            )
            db.session.add(reg)
            ev.registered_count += 1

        db.session.add(
            Notification(
                recipient_id=att1.id,
                title="Welcome to EventEase",
                content="Your attendee profile is active. Browse upcoming conferences and manage your check-in passes from your dashboard.",
                notification_type="WELCOME",
            )
        )
        db.session.commit()
