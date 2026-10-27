# UniSphere API & Integration Architecture

## 1. Architectural Philosophy

UniSphere intentionally **does not expose a standalone REST or GraphQL microservice layer** (e.g., Express or FastAPI), avoiding unnecessary architectural sprawl and redundant authentication systems.

Instead, UniSphere communicates via two native Odoo integration layers:
1. **Internal ORM & RPC Dispatch (Backend Administration):** Handled transparently by Odoo 19's JSON-RPC protocol (`/web/dataset/call_kw`) between the OWL frontend and Python ORM models.
2. **Student Portal Web Routes (`http.Controller`):** Authenticated HTTP endpoints delivering server-rendered QWeb interfaces and JSON endpoints for the student experience.

---

## 2. Planned Student Portal Routes (Phase 9)

All student portal endpoints require authenticated session cookies associated with a user belonging to `unisphere_university.group_unisphere_student`.

### A. Portal Home / Dashboard
- **Route:** `GET /my/unisphere`
- **Auth:** `user` (Enforces authenticated portal user)
- **Controller Method:** `UniSpherePortal.portal_my_unisphere()`
- **Response:** QWeb Template `unisphere_university.portal_my_dashboard`
- **Context Delivered:** Active semester info, enrolled course sections, aggregate attendance percentage, published GPA, outstanding fee balance.

### B. Course Roster & Details
- **Route:** `GET /my/unisphere/courses/<int:section_id>`
- **Auth:** `user`
- **Security Check:** Verifies that `section_id` exists in `student.enrollment_ids.section_id`. Returns `403 Forbidden` if a student attempts to query another section.
- **Context Delivered:** Section schedule, instructor name, room, syllabus, class-by-class attendance, published assessment marks.

### C. Fee Challan & Payment Status
- **Route:** `GET /my/unisphere/fees`
- **Auth:** `user`
- **Security Check:** Fetches records where `student_id.user_id = request.uid`.
- **Context Delivered:** List of fee challan records, due dates, paid amounts, payment instructions, and verification state.

---

## 3. Internal ORM Service API Patterns

For programmatic interaction between models, UniSphere uses idiomatic Odoo Python methods:

### Course Enrollment Service
```python
# Model: unisphere.course.section
def action_enroll_student(self, student_id):
    """
    Enrolls a student into the section with strict validation:
    - Checks section capacity
    - Verifies active registration term
    - Ensures student has no existing active enrollment in the section
    """
```

### Grade Publication Service
```python
# Model: unisphere.assessment
def action_publish_grades(self):
    """
    Transitions assessment state to 'published'.
    Ensures marks are locked from unauthorized modifications and visible on Student Portal.
    """
```

### Attendance Summary Computation
```python
# Model: unisphere.enrollment
@api.depends('section_id.attendance_ids.state')
def _compute_attendance_rate(self):
    """
    Calculates percentage of attended sessions: (Present / Total Held Sessions) * 100.
    """
```
