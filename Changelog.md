# UniSphere Changelog

All notable changes to the UniSphere University ERP project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Phase 8: Executive Academic Dashboard] - 2026-10-29

### Added
- Implemented `unisphere.dashboard` backend service model:
  - Aggregates institutional analytics across terms, departments, courses, students, faculty, grades, attendance, and bursar ledger.
  - Dynamically calculates:
    - 4 Core KPIs: Active Enrollments, Faculty & Offerings, Average Attendance Rate, and Fee Realization Velocity.
    - Department capacity breakdown with customized color tokens.
    - Multi-segment fee velocity: Collected ($4,050.00 / 64.8%), Pending ($700.00 / 11.2%), Overdue ($1,500.00 / 24.0%).
    - Actionable compliance alerts (attendance risks $< 75\%$ and overdue bursar invoices).
- Implemented OWL 2 Client Action `unisphere_dashboard`:
  - `static/src/dashboard/dashboard.js`: Interactive OWL component using `@odoo/owl` (`useState`, `onWillStart`) and Odoo services (`orm`, `action`, `notification`).
  - Interactive academic term switcher dynamically reloading metrics on change.
  - 1-click quick action headers: Add Student, New Section, Take Attendance (launching wizard modal), and Issue Challan.
  - Clickable KPI cards and table rows drilling directly into Odoo backend list/form views.
  - Alert action triggers opening specific student dossiers or overdue vouchers.
- Created `static/src/dashboard/dashboard.scss`:
  - Implemented the Stitch design tokens: Deep Navy `#172554`, Dark Primary `#000f3f`, Academic Blue `#2563EB`, Academic Teal `#0F766E`, Neutral Canvas `#F8FAFC`.
  - Modern card hover elevations, multi-segment progress tracks, and clean data tables.
- Created `static/src/dashboard/dashboard.xml`:
  - Native OWL QWeb template with responsive grid layouts, status chips, avatar circles, and alert banners.
- Created `views/dashboard_views.xml`:
  - Registered client action `action_unisphere_dashboard` (`tag: unisphere_dashboard`).
- Updated `views/menus.xml`:
  - Configured root navigation menu `menu_unisphere_root` and `menu_unisphere_overview` to default directly to the Executive Dashboard.
- Registered asset bundle `web.assets_backend` in `__manifest__.py` and bumped version to `19.0.8.0.0`.
- Added automated unit test suite `tests/test_dashboard.py` (3 test cases validating data structure, metric ranges, department breakdown, fee velocity calculations, and term scoping).

### Validated
- Passed 37/37 automated unit tests across all 8 phases with 0 failures, 0 errors, and 0 warnings.
- Verified live PostgreSQL 17 database metrics:
  - Active Enrollments: 7
  - Total Students: 4
  - Faculty: 4 (100% active)
  - Active Sections: 6
  - Term CGPA Average: 3.65 / 4.00
  - Institutional Attendance Rate: 75.0%
  - Total Fee Invoiced: $6,250.00 | Realized: $4,050.00 (64.8%) | Receivables: $2,200.00
  - Live alerts: Low attendance (Muhammad Usman 50.0%) and Overdue Tuition (Muhammad Usman $1,500.00).

---

## [Phase 7: Scoped Fee Management] - 2026-10-29

### Added
- Implemented `unisphere.fee` student fee & challan ledger model:
  - Sequence generator: `ir.sequence` (`NUT-FEE-%(year)s-####`) generating unique institutional voucher IDs.
  - Core classifications: Tuition (per term), Admission, Lab & Tech, Library, Exam, Hostel, and Miscellaneous.
  - Financial calculations: `amount_due`, `amount_paid`, and computed real-time `balance_due`.
  - Lifecycle state machine: `draft`, `posted` (issued/unpaid), `partial` (partially paid), `paid` (settled in full), `overdue` (unpaid past due date), and `cancelled`.
  - Payment tracking: `payment_method` (`bank_transfer`, `cash`, `online`, `scholarship`), `payment_reference`, and `payment_date`.
  - Constraints: rejects negative amounts, overpayments exceeding total balance due, and due dates earlier than issue dates.
- Implemented `unisphere.fee.payment.wizard`:
  - 1-click modal payment registration dialog allowing bursars to record full or partial payments.
  - Automatically updates voucher balance, updates state to `partial` or `paid`, and writes audit receipt notifications directly into the fee chatter log.
  - Validation: rejects zero/negative payment amounts and payments exceeding current balance due.
- Enhanced `unisphere.student`:
  - Financial rollups: `fee_ids` one-to-many link, `total_invoiced`, `total_paid`, and `balance_due`.
  - Computed institutional financial status `fee_status` with dynamic badges:
    - `clear` (all dues paid, Green)
    - `dues_pending` (outstanding balance within due date, Orange)
    - `overdue` (unpaid dues past due date, Red)
  - Bursar smart button **Fee Dues** on student form with real-time balance display and 1-click navigation to the student's fee ledger.
  - Notebook tab **Bursar Ledger** embedded directly in the student profile form.
- Created declarative XML views:
  - List View with sum aggregations for Total Invoiced, Total Collected, and Outstanding Dues.
  - Form View with statusbar, payment action header button, and chatter.
  - Pivot Matrix View for financial analysis across departments, academic terms, and fee types.
  - Search View with quick filters (`filter_unpaid`, `filter_paid`, `filter_overdue`) and grouping.
  - Modal form view for `unisphere.fee.payment.wizard`.
- Added navigation sub-menu under **Bursar & Fees**: **Fee Challans & Invoices**.
- Loaded realistic Fall 2024 demo fee challans:
  - Ayesha Malik: $1,500 Tuition (Paid in full via Bank Transfer) + $250 Lab Fee (Paid in full via Cash) $\rightarrow$ **Clear** ($0 balance).
  - Bilal Ahmed Khan: $1,500 Tuition ($800 paid online, $700 pending) $\rightarrow$ **Dues Pending** ($700 balance).
  - Muhammad Usman: $1,500 Tuition ($0 paid, due 2024-09-15) $\rightarrow$ **Overdue** ($1,500 balance).
  - Zainab Fatima: $1,500 Tuition (100% Merit Scholarship waiver) $\rightarrow$ **Clear** ($0 balance).
- Created automated test suite (`tests/test_fees.py`) with 9 unit tests covering sequence generation, balance math, workflow transitions, overdue date triggers, negative/excess validation, payment wizard flow, and student profile rollups.

### Validated
- Passed 34/34 automated unit tests across all 7 phases with 0 failures, 0 errors, and 0 warnings.
- Verified live PostgreSQL 17 database metrics:
  - Total institutional billings: $6,250.00
  - Total collections & waivers: $4,050.00
  - Total outstanding receivables: $2,200.00 (Bilal $700 + Usman $1,500)
- Hot-reloaded container services and confirmed clean web client UI state.

---

## [Phase 6: Continuous Assessments & Gradebook Engine] - 2026-10-29

### Added
- Implemented `unisphere.assessment` course component model:
  - Supports types: Quiz, Assignment, Midterm Exam, Term Project, Final Exam, Lab Practical.
  - Evaluation parameters: `max_marks`, `weightage` (%), `due_date`, and lifecycle state machine (`draft`, `announced`, `grading`, `published`).
  - Validation: rejects non-positive marks, weightage out of range (1-100%), and ensures total section assessment weightage does not exceed 100%.
  - Computed class metrics: `graded_count` and `average_score` (%).
  - Header actions: Announce, Enter Grades (modal wizard), and Publish Grades.
- Implemented `unisphere.grade` student marks entry model:
  - Links Student $\leftrightarrow$ Assessment $\leftrightarrow$ Course Section $\leftrightarrow$ Enrollment.
  - Automatically computes score `percentage`, official `letter_grade` (A, A-, B+, B, B-, C+, C, D, F), and standard 4.0 `grade_point`.
  - Database constraint: `UNIQUE(assessment_id, student_id)`.
  - Validation: rejects marks exceeding maximum assessment points or marks for students not enrolled.
- Implemented `unisphere.grade.wizard` & `unisphere.grade.wizard.line`:
  - 1-click batch grade entry dialog for faculty, auto-populating enrolled students in an interactive roster grid.
  - Re-evaluates assessment state and propagates recalculated scores.
- Enhanced `unisphere.enrollment`:
  - Computed composite progress score `final_grade`, normalized across evaluated assessment weightages.
  - Computed official course `letter_grade`, `grade_point`, and boolean `is_passed`.
  - Embedded Assessment Marks subtable and Grade Performance summary card in enrollment form view.
- Enhanced `unisphere.student`:
  - Institutional cumulative `gpa` (Grade Point Average weighted by course credit hours) and `earned_credits`.
  - Smart button **CGPA** with trophy icon and color-coded status badges.
- Enhanced `unisphere.course.section`:
  - Smart buttons **Assessments** and **Gradebook**.
  - Embedded Assessments & Weightage notebook tab.
- Created declarative XML views:
  - Assessment List, Form, and Search views.
  - Gradebook List, Pivot Matrix, Form, and Search views.
  - Quick Grade Entry Wizard modal form.
- Added navigation submenus under **Grades & Exams**: **Course Assessments** and **Gradebook Matrix**.
- Loaded realistic demo assessments (5 components totaling 100% weightage) and published evaluation marks across CS-101 Section 1A cohort.
- Added automated unit test suite (`tests/test_assessments_grades.py`) with 7 test cases covering weightage bounds, letter grade scale mapping, duplicate grade rejection, max marks enforcement, unenrolled rejection, composite GPA math, and batch wizard execution.

### Validated
- Passed 25/25 automated unit tests with 0 failures, 0 errors, and 0 warnings.
- Verified live database metrics:
  - Ayesha Malik: 93.6% Course Score $\rightarrow$ Grade **A** (4.00 GPA), 3 earned credits
  - Bilal Ahmed Khan: 78.0% Course Score $\rightarrow$ Grade **B+** (3.30 GPA), 3 earned credits
  - Muhammad Usman: 47.8% Course Score $\rightarrow$ Grade **F** (0.00 GPA, Needs Academic Counseling)
  - CS-101 Section 1A: Midterm Avg 71.7%, Quiz 1 Avg 73.3%, Assignment 1 Avg 76.0%

---

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
