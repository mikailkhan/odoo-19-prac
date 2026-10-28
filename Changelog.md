# UniSphere Changelog

All notable changes to the UniSphere University ERP project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Phase 5: Attendance Tracking] - 2026-10-28

### Added
- Implemented `unisphere.attendance` session record model:
  - Links Student $\leftrightarrow$ Course Section $\leftrightarrow$ Academic Term $\leftrightarrow$ Enrollment.
  - Tracking fields for `class_date`, status `state` (`present`, `late`, `absent`), and observational `remarks`.
  - Database-level unique constraint (`UNIQUE(student_id, section_id, class_date)`) preventing duplicate records on the same session date.
  - Python `@api.constrains` preventing future dates and rejecting attendance for students not actively enrolled in the course section.
- Implemented `unisphere.attendance.wizard` & `unisphere.attendance.wizard.line`:
  - 1-click batch attendance entry modal allowing faculty to quickly mark attendance for the whole section roster.
  - Automatically loads enrolled students with default `present` status.
  - Upserts in place if a session for that date was already started.
- Enhanced `unisphere.enrollment`:
  - Computed attendance compliance counters: `total_sessions`, `attended_sessions`, `absent_sessions`.
  - Stored `attendance_rate` percentage (attended / total * 100), with dynamic `< 75%` danger badges.
  - Embedded Attendance History subtable in enrollment form view.
- Enhanced `unisphere.course.section`:
  - Live session metrics: `total_sessions_held`, `average_attendance_rate`, and `attendance_count`.
  - Header button **Take Attendance** (opens modal wizard).
  - Stat smart button **Attendance** and embedded Attendance Log tab.
- Enhanced `unisphere.student`:
  - Institutional cumulative `attendance_rate` progress bar and stat counter.
  - Smart button **Attendance Records** filtering all sessions attended by the student.
- Created declarative XML views:
  - Attendance List view with status badges, date, and remark columns.
  - Attendance Form view with radio selector and chatter tracking.
  - Attendance Search view with preset filters (Present, Late, Absent, Today's Sessions) and grouping by Section/Date/Status.
  - Quick Attendance Wizard modal form view with roster line items.
- Registered **Attendance Register** menu under **Class Operations**.
- Pre-populated realistic demo attendance sessions for Fall 2024 CS-101 Section 1A showing varying student attendance rates (Ayesha Malik 100%, Bilal Khan 75%, Muhammad Usman 50% triggering attendance warning).
- Added automated unit test suite (`tests/test_attendance.py`) testing enrollment link compute, unique constraint rejection, future date prevention, unenrolled student rejection, percentage calculation, and batch wizard execution.

### Validated
- Passed 18/18 automated unit tests across all test suites with 0 failures and 0 errors.
- Verified live database metrics:
  - Muhammad Usman: 50.0% (4 sessions)
  - Bilal Ahmed Khan: 75.0% (4 sessions)
  - Ayesha Malik: 100.0% (4 sessions)
  - CS101 Section 1A: 4 sessions held, 75.0% average attendance rate.

---

## [Phase 4: Course Section Enrollment] - 2026-10-27

### Added
- Implemented `unisphere.enrollment` model:
  - Links Student $\leftrightarrow$ Course Section $\leftrightarrow$ Academic Term.
  - Relational fields for automatic course, term, and department tracking.
  - Lifecycle state machine: `draft` (Pending Approval), `enrolled` (Confirmed), `dropped` (Withdrawn), `completed` (Term Completed).
  - Enforced duplicate prevention via `models.Constraint('UNIQUE(student_id, section_id)', ...)`.
  - Enforced strict capacity validation preventing enrollments when a section's limit is reached.
- Refactored `unisphere.course.section`:
  - Dynamically computes `enrolled_count` and `seats_available` based on active confirmed enrollments.
  - Added "Class Roster" smart button and embedded student roster table.
- Enhanced `unisphere.student`:
  - Dynamically computes `enrollment_count` (active registered courses).
  - Added "Active Courses" smart button and embedded enrolled courses table.
- Created declarative XML views:
  - Enrollment List view with status badges and term/section filters.
  - Enrollment Form view with state machine action buttons and chatter.
  - Enrollment Pivot view for term/department distribution analytics.
- Added **Enrollment Roster** menu under **Class Operations**.
- Pre-populated realistic demo enrollments matching the Stitch admissions table (5 active enrollments).
- Added automated unit test suite (`tests/test_enrollment.py`) testing duplicate enrollment prevention, section capacity limits, and seat freeing on withdrawal.

### Validated
- Passed 12/12 automated unit tests across all test suites with 0 failures and 0 errors.
- Verified database records: 5 confirmed enrollments across Fall 2024 active sections.

---

## [Phase 3: Students and Faculty] - 2026-10-27

### Added
- Implemented `unisphere.student` profile model:
  - Linked to core `res.partner` for contact identity (name, email, phone, avatar picture).
  - Unique matriculation ID (`student_id`) with Odoo 19 `models.Constraint`.
  - Degree programs (`bs_cs`, `bs_se`, `bs_ee`, `bs_ai`, `bba`, `ms_cs`), admission dates, current term, and enrollment lifecycle state machine (`draft`, `enrolled`, `suspended`, `graduated`, `withdrawn`).
  - Personal demographics (gender, date of birth, blood group).
- Implemented `unisphere.faculty` profile model:
  - Linked to `res.partner` and internal `res.users` for ERP system access.
  - Unique staff identifier (`faculty_id`) with `models.Constraint`.
  - Academic ranks (Professor, Associate Professor, Assistant Professor, Lecturer, Adjunct Fellow).
  - Qualifications, areas of specialization, and reverse linkage to assigned course sections.
  - Smart button with live counter for active teaching sections.
- Refactored `unisphere.course.section.instructor_id` to link directly to `unisphere.faculty`.
- Created declarative XML views:
  - Student and Faculty List views with badge widgets and contact fields.
  - Student and Faculty Kanban views featuring responsive `<aside>`, `<main>`, and `<footer>` cards.
  - Student and Faculty Form views with avatars, contact tabs, and `<chatter/>`.
  - Search views with group-by filters (Department, Program, Academic Term, Designation).
- Submenu navigation added under **Students & Faculty** in [menus.xml](file:///Users/mikailkhan/Documents/WebDev/Practice/odoo19-local/addons/unisphere_university/views/menus.xml).
- Added realistic demo records matching the Stitch roster:
  - Faculty: Dr. Eleanor Vance (HoD CS), Dr. Tariq Mahmood, Engr. Farhan Ali, Dr. Sarah Jenkins.
  - Students: Ayesha Malik (`NUT-2024-CS-0142`), Bilal Ahmed Khan (`NUT-2024-EE-0089`), Zainab Fatima (`NUT-2024-SE-0311`), Muhammad Usman (`NUT-2024-AI-0105`).
- Added automated unit test suite (`tests/test_students_faculty.py`) covering unique constraints, contact synchronization, and smart button section counts.

### Validated
- Passed 9/9 automated unit tests across all test suites with 0 failures and 0 errors.
- Verified database population: 4 students and 4 faculty members with complete relational linkages.

---

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
