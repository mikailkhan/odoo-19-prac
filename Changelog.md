# UniSphere Changelog

All notable changes to the UniSphere University ERP project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Phase 2: Academic Foundation] - 2026-10-27

### Added
- Implemented core Academic Foundation models:
  - `unisphere.department`: Code, Name, HoD reference, computed course count, and uppercase code validation.
  - `unisphere.academic.term`: Code, Name, Start/End dates, registration windows, state machine (Draft, Active, Closed).
  - `unisphere.course`: Code, Title, Department reference, credit hours validation (1-6), and computed display name.
  - `unisphere.course.section`: Specific term offerings linking Course + Term, classroom, schedule, capacity limits, and seats available calculations.
- Integrated Odoo 19 `models.Constraint` for database-level unique constraints on codes and term sections.
- Created declarative XML views:
  - List views with modern `<list>` syntax and status badges.
  - Form views with chatter widgets (`<chatter/>`) and smart buttons with stat counters.
  - Search views with group-by filters.
- Linked window actions to the primary UniSphere navigation menus.
- Loaded comprehensive academic demo data for Northstar University of Technology (5 departments, 3 terms, 6 courses, 6 active Fall 2024 sections).
- Added automated unit test suite (`tests/test_academic_foundation.py`) covering date checks, credit hours, capacity, and uniqueness.

### Validated
- Passed 5/5 automated unit tests with zero failures or errors.
- Verified database population: 5 departments, 3 terms, 6 courses, 6 course sections.

---

## [Phase 1: Module Skeleton] - 2026-10-27

### Added
- Initialized Git version control repository with `.gitignore` excluding temporary files and Stitch design reference directories.
- Created `addons/unisphere_university` module structure:
  - `__manifest__.py`: Module metadata, LGPL-3 licensing, dependencies (`base`, `mail`, `portal`), and view declarations.
  - `__init__.py` & `models/__init__.py`: Python initialization packages.
  - `security/groups.xml`: Defined `UniSphere University` category and roles for Administrator, Faculty Member, and Student Portal User.
  - `security/ir.model.access.csv`: Foundational access control list file.
  - `views/menus.xml`: Root and top-level category navigation hierarchy (Academics, Students & Faculty, Class Operations, Grades & Exams, Bursar & Fees, Configuration).
  - `static/description/icon.png`: UniSphere custom branded app icon.
- Created foundational documentation suite: `README.md`, `Architecture.md`, `API.md`, `Decisions.md`, `Changelog.md`, `Future.md`.

### Validated
- Confirmed module syntax and installation in local Dockerized Odoo 19 instance against database `nutech`.

---

## [Phase 0: Discovery & Architecture] - 2026-10-27

### Added
- Completed discovery analysis of Docker containers (`odoo:19.0`, `postgres:17`), database `nutech`, and Stitch design assets.
- Formulated Entity Relationship Diagram (ERD), security role matrix, and screen-to-view mapping.
