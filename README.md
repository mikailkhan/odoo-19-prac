# UniSphere — Mini University Management System (Odoo 19)

**UniSphere** is a modern University ERP demonstration built natively on **Odoo 19** for the fictional **Northstar University of Technology (NUT)**. 

Designed with an enterprise architectural foundation, UniSphere bridges internal academic administration (Registrar, Deans, Faculty, Bursar) with a dedicated, responsive Student Portal.

---

## 🏛️ System Features

1. **Academic Architecture:** Academic departments, academic terms/semesters, course catalogs, and term offerings (Course Sections).
2. **Student & Faculty Management:** Institutional profiles linked directly to native Odoo contacts (`res.partner`) and authenticated users (`res.users`).
3. **Enrollments:** Section rosters with automatic capacity enforcement and duplicate prevention.
4. **Attendance Tracking:** Session-based class attendance (Present, Absent, Late) with automatic summary calculations.
5. **Continuous Assessment & Gradebook:** Quizzes, assignments, midterms, and finals with strict range validation and publication status controls.
6. **Bursar & Fee Ledgers:** Demonstration fee ledger tracking student dues, challan numbers, and collection velocity.
7. **Executive Dashboard:** Record-backed KPI cards, department distributions, and institutional deadline tracking.
8. **Student Portal:** External, self-service web portal for students to review course schedules, attendance rates, and term grades.
9. **AI Academic Assistant (Planned):** Scoped, read-only academic chatbot with a deterministic mock mode.

---

## 🚀 Prerequisites & Local Setup

### Prerequisites
- Docker & Docker Compose
- Web browser (Chrome / Safari / Firefox)

### Starting the Environment
The application is pre-configured with Docker Compose:
```bash
# Create your local config from the template, then edit the placeholder passwords
cp odoo.conf.example odoo.conf

# Start PostgreSQL and Odoo 19 containers
docker compose up -d

# Check container health
docker compose ps
```

The system will be accessible at:
- **University Institutional Homepage:** [http://127.0.0.1:8069](http://127.0.0.1:8069)
- **Student Academic Portal:** [http://127.0.0.1:8069/my/unisphere](http://127.0.0.1:8069/my/unisphere)
- **Administrative ERP Backend:** [http://127.0.0.1:8069/odoo](http://127.0.0.1:8069/odoo)
- **Target Database:** `nutech`

### 🎭 Instant 1-Click Demo Personas
Visitors to the homepage ([http://127.0.0.1:8069](http://127.0.0.1:8069)) or login page can use the **1-Click Demo Login** buttons:

| Persona | Role | Email | Password | Showcase Focus |
| :--- | :--- | :--- | :--- | :--- |
| **Ayesha Malik** | Honor Student | `student.ayesha@northstar.edu` | `student123` | 4.00 CGPA, Dean's List, 100% Attendance, Clear Balance |
| **Muhammad Usman** | At-Risk Student | `student.usman@northstar.edu` | `student123` | 50.0% Attendance Warning (&lt;75%), $1,500 Overdue Tuition Challan |
| **Mikail Khan** | Super Admin | `khanmikail1002@gmail.com` | `admin123` | Executive OWL Dashboard, Registrar, Dean, & Bursar Access |

---

## 📦 Module Management

### Install or Upgrade the Module
To update or reinstall `unisphere_university` directly inside the running container:
```bash
# Update/Install module in database nutech
docker exec odoo19-local-odoo-1 odoo -u unisphere_university -d nutech --stop-after-init

# Restart Odoo service container to pick up changes
docker compose restart odoo
```

---

## 📚 Project Documentation

- [Architecture.md](file:///Users/mikailkhan/Documents/WebDev/Practice/odoo19-local/Architecture.md) — Comprehensive technical architecture, ORM design, security boundaries, and ASCII diagrams.
- [API.md](file:///Users/mikailkhan/Documents/WebDev/Practice/odoo19-local/API.md) — Internal ORM patterns, portal controllers, routes, and authentication specifications.
- [Decisions.md](file:///Users/mikailkhan/Documents/WebDev/Practice/odoo19-local/Decisions.md) — Architectural Decision Records (ADRs) tracking design rationale.
- [Changelog.md](file:///Users/mikailkhan/Documents/WebDev/Practice/odoo19-local/Changelog.md) — Phased progress log.
- [Future.md](file:///Users/mikailkhan/Documents/WebDev/Practice/odoo19-local/Future.md) — Planned enhancements, known limitations, and roadmap.
