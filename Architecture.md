# UniSphere Architecture & Engineering Guide

## 1. Executive Summary

UniSphere is built natively on **Odoo 19 Community Edition**, adhering to standard ERP design principles. Instead of deploying disparate decoupled stacks (such as React + Express + Prisma), UniSphere leverages Odoo's declarative, metadata-driven architecture to deliver a high-performance backend administrative interface alongside a secured, server-rendered student portal.

---

## 2. High-Level Architecture Diagram

```text
+-----------------------------------------------------------------------------------------+
|                                     CLIENT LAYER                                        |
|                                                                                         |
|  +--------------------------------------------+    +---------------------------------+  |
|  |           Internal ERP Backend             |    |      Student Web Portal         |  |
|  |     (Registrars, Deans, Faculty)           |    |     (Enrolled Students)         |  |
|  |  Views: List, Form, Kanban, Pivot, Graph   |    |  QWeb HTML5 Templates + Portal  |  |
|  |  Client-side OWL (Odoo Web Library) v19    |    |  Tailwind/CSS Academic Tokens   |  |
|  +--------------------------------------------+    +---------------------------------+  |
+-----------------------------------------------------------------------------------------+
                                     |                                    |
                          JSON-RPC / Web Session              HTTP /session /my/...
                                     |                                    |
+------------------------------------+------------------------------------+---------------+
|                                  ODOO 19 APPLICATION SERVER                             |
|                                                                                         |
|  +-----------------------------------------------------------------------------------+  |
|  |                                Security & Dispatch Layer                          |  |
|  |  • Authentication & Session Management (ir.http / res.users)                      |  |
|  |  • Role-Based Access Control (res.groups / ir.model.access.csv)                   |  |
|  |  • Row-Level Security Rules (ir.rule - Domain Filters)                            |  |
|  +-----------------------------------------------------------------------------------+  |
|                                            |                                            |
|  +-----------------------------------------------------------------------------------+  |
|  |                              UniSphere Business Models                            |  |
|  |                                                                                   |  |
|  |   [unisphere.department]       [unisphere.academic.term]     [unisphere.course]   |  |
|  |             |                              |                           |          |  |
|  |             +--------------+---------------+---------------------------+          |  |
|  |                            |                                                      |  |
|  |                [unisphere.course.section]                                         |  |
|  |                   /                   \                                           |  |
|  |      [unisphere.enrollment]     [unisphere.assessment]                            |  |
|  |          /              \                 |                                       |  |
|  |  [unisphere.attendance] [unisphere.fee] [unisphere.grade]                         |  |
|  +-----------------------------------------------------------------------------------+  |
|                                            |                                            |
|  +-----------------------------------------------------------------------------------+  |
|  |                                Odoo Core Integration                              |  |
|  |  • res.partner (Contact Book & Identity)                                          |  |
|  |  • mail.thread & mail.activity.mixin (Audit Trail, Notes, Chatter)                |  |
|  |  • portal.mixin (Web Portal URL & Security Tokens)                                |  |
|  +-----------------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------------+
                                             |
                                  Odoo ORM (SQL Generation)
                                             |
+--------------------------------------------+--------------------------------------------+
|                                    PERSISTENCE LAYER                                    |
|                                                                                         |
|                           PostgreSQL 17 Relational Database                             |
|                           (nutech database cluster)                                     |
+-----------------------------------------------------------------------------------------+
```

---

## 3. PERN vs. Odoo 19 Architectural Equivalents

For engineers with modern JavaScript/TypeScript and PERN stack backgrounds:

| Functional Responsibility | PERN Stack Paradigm | Odoo 19 Framework Paradigm |
| :--- | :--- | :--- |
| **Data Schema Definition** | Prisma Schema / SQL DDL | Python classes inheriting `models.Model` with typed fields (`fields.Char`, `fields.Many2one`). |
| **Database Migrations** | `prisma migrate` / Knex scripts | Automatic declarative migrations executed during module upgrade (`odoo -u <addon>`). |
| **API Endpoints** | Express routes (`app.get('/api/students')`) | Native ORM RPC dispatch for backend views; `http.Controller` (`@http.route`) for portal endpoints. |
| **Row-Level Security** | Custom Express middleware with manual SQL `WHERE` | Declarative XML `ir.rule` injecting domain constraints directly into SQL queries. |
| **Admin UI Generation** | Retool / React Admin / Hand-rolled forms | Declarative XML views (`<list>`, `<form>`, `<kanban>`, `<search>`) rendered dynamically by OWL. |
| **State Machine Management**| Custom reducers or state libraries | `fields.Selection` with `tracking=True` and action methods transitioning states. |
| **Audit Trails & Logs** | Event sourcing or manual audit tables | Inheriting `mail.thread` automatically provisions message logging and chatter widgets. |

---

## 4. Module Directory Structure

The `unisphere_university` module follows Odoo's official structural standard:

```text
addons/unisphere_university/
├── __init__.py                  # Root package initializer
├── __manifest__.py              # Manifest metadata, dependencies, and data loading list
├── models/                      # Python business logic & ORM schemas
│   ├── __init__.py
│   ├── department.py            # Phase 2
│   ├── academic_term.py         # Phase 2
│   ├── course.py                # Phase 2
│   ├── course_section.py        # Phase 2
│   ├── student.py               # Phase 3
│   ├── faculty.py               # Phase 3
│   ├── enrollment.py            # Phase 4
│   ├── attendance.py            # Phase 5
│   ├── assessment.py            # Phase 6
│   ├── grade.py                 # Phase 6
│   └── fee.py                   # Phase 7
├── security/                    # Authorization definitions
│   ├── groups.xml               # Security groups (Admin, Faculty, Student)
│   ├── ir.model.access.csv      # Model Access Control Lists (ACLs)
│   └── record_rules.xml         # Scoped row-level record rules
├── views/                       # Declarative UI layouts
│   ├── menus.xml                # Top-level and category navigation menus
│   ├── department_views.xml     # Phase 2
│   ├── academic_views.xml       # Phase 2
│   ├── course_views.xml         # Phase 2
│   └── ...
├── controllers/                 # Web controllers for Student Portal (Phase 9)
│   ├── __init__.py
│   └── portal.py
├── static/                      # Static web assets
│   └── description/
│       └── icon.png             # Module app launcher icon
└── tests/                       # Automated business logic tests
    └── __init__.py
```

---

## 5. Security & Authorization Matrix

UniSphere defines three distinct operational security levels:

| Role | Group External ID | Backend Access (`/odoo`) | Portal Access (`/my`) | Permissions Scope |
| :--- | :--- | :--- | :--- | :--- |
| **University Administrator** | `group_unisphere_admin` | Full | Full | Unrestricted CRUD across all academic models, grade publication, and fee ledgers. |
| **Faculty Member** | `group_unisphere_faculty` | Restricted | Read-Only | Read access to courses/students. Write access restricted via `ir.rule` strictly to their assigned sections for attendance and assessments. |
| **Student** | `group_unisphere_student` | None (Denied) | Full | Read-only access to their own student profile, enrolled courses, attendance records, published grades, and fee balances. |
| **Public Visitor** | `base.group_public` | None (Denied) | None (Denied) | Zero access to university records. |
