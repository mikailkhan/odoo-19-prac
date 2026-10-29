# -*- coding: utf-8 -*-
from odoo import models, api, fields, _


class UnisphereDashboard(models.AbstractModel):
    _name = 'unisphere.dashboard'
    _description = 'Institutional Executive Dashboard Service'

    @api.model
    def get_dashboard_data(self, term_id=None):
        Term = self.env['unisphere.academic.term']
        Student = self.env['unisphere.student']
        Faculty = self.env['unisphere.faculty']
        Section = self.env['unisphere.course.section']
        Enrollment = self.env['unisphere.enrollment']
        Fee = self.env['unisphere.fee']
        Department = self.env['unisphere.department']

        # Determine active term
        terms = Term.search([], order='start_date desc')
        active_term = Term.browse(term_id) if term_id else terms.filtered(lambda t: t.state == 'active')[:1]
        if not active_term and terms:
            active_term = terms[0]

        # Scope filters
        term_domain = [('term_id', '=', active_term.id)] if active_term else []
        student_domain = [('current_term_id', '=', active_term.id)] if active_term else []

        # 1. Total counts
        students = Student.search(student_domain) if student_domain else Student.search([])
        total_students_count = len(students)
        faculty_count = Faculty.search_count([])
        sections = Section.search(term_domain) if term_domain else Section.search([])
        active_sections_count = len(sections)
        enrollments = Enrollment.search(term_domain) if term_domain else Enrollment.search([])
        active_enrollments_count = len(enrollments.filtered(lambda e: e.state == 'enrolled'))

        # 2. Academic Performance & Attendance
        valid_gpas = [s.gpa for s in students if s.gpa > 0.0]
        avg_gpa = round(sum(valid_gpas) / len(valid_gpas), 2) if valid_gpas else 0.0

        attendance_rates = [s.attendance_rate for s in students if s.attendance_count > 0]
        avg_attendance = round(sum(attendance_rates) / len(attendance_rates), 1) if attendance_rates else 0.0

        # 3. Bursar & Financial Metrics
        fees = Fee.search(term_domain) if term_domain else Fee.search([])
        total_invoiced = sum(fees.mapped('amount_due'))
        total_collected = sum(fees.mapped('amount_paid'))
        total_receivable = sum(fees.mapped('balance_due'))
        collection_rate = round((total_collected / total_invoiced * 100), 1) if total_invoiced > 0 else 0.0

        # Overdue and Pending breakdown
        today = fields.Date.today()
        overdue_amount = sum(fees.filtered(lambda f: f.state == 'overdue' or (f.due_date and f.due_date < today and f.balance_due > 0)).mapped('balance_due'))
        pending_amount = max(0.0, total_receivable - overdue_amount)

        # 4. Department Breakdown
        dept_colors = ['#2563EB', '#0F766E', '#3B82F6', '#6366F1', '#10B981', '#F59E0B']
        departments = Department.search([], order='name asc')
        dept_data = []
        for idx, dept in enumerate(departments):
            dept_students = students.filtered(lambda s: s.department_id.id == dept.id)
            dept_sections = sections.filtered(lambda sec: sec.department_id.id == dept.id)
            dept_enrollments = enrollments.filtered(lambda e: e.course_id.department_id.id == dept.id)
            dept_attendance_rates = [s.attendance_rate for s in dept_students if s.attendance_count > 0]
            dept_avg_att = round(sum(dept_attendance_rates) / len(dept_attendance_rates), 1) if dept_attendance_rates else 100.0

            dept_data.append({
                'id': dept.id,
                'name': dept.name,
                'code': dept.code,
                'student_count': len(dept_students),
                'section_count': len(dept_sections),
                'enrollment_count': len(dept_enrollments),
                'avg_attendance': dept_avg_att,
                'color': dept_colors[idx % len(dept_colors)],
            })

        # 5. Recent Student Roster (up to 6)
        recent_students = []
        for s in students[:6]:
            is_low_att = bool(s.attendance_count > 0 and s.attendance_rate < 75.0)
            recent_students.append({
                'id': s.id,
                'student_id': s.student_id,
                'name': s.name,
                'email': s.email or '',
                'department': s.department_id.name if s.department_id else 'General',
                'program': dict(s._fields['program'].selection).get(s.program, s.program),
                'gpa': f"{s.gpa:.2f}",
                'attendance_rate': f"{s.attendance_rate:.1f}%",
                'is_low_attendance': is_low_att,
                'fee_status': s.fee_status,
                'balance_due': f"${s.balance_due:.2f}",
            })

        # 6. Actionable Alerts
        alerts = []
        # Low attendance alerts
        for s in students.filtered(lambda st: st.attendance_count > 0 and st.attendance_rate < 75.0):
            alerts.append({
                'id': f"att_{s.id}",
                'type': 'danger',
                'category': 'Attendance Alert',
                'title': f'Low Attendance Warning: {s.name}',
                'description': f'{s.name} ({s.student_id}) attendance is {s.attendance_rate:.1f}%, below the 75% threshold.',
                'action_model': 'unisphere.student',
                'action_res_id': s.id,
                'action_label': 'View Student',
            })

        # Overdue fee alerts
        overdue_fees = fees.filtered(lambda f: f.state == 'overdue' or (f.due_date and f.due_date < today and f.balance_due > 0))
        for f in overdue_fees[:3]:
            alerts.append({
                'id': f"fee_{f.id}",
                'type': 'warning',
                'category': 'Bursar Defaulter',
                'title': f'Overdue Tuition: {f.student_id.name}',
                'description': f'Challan {f.challan_number} for ${f.balance_due:.2f} due on {f.due_date} is outstanding.',
                'action_model': 'unisphere.fee',
                'action_res_id': f.id,
                'action_label': 'Inspect Challan',
            })

        return {
            'terms': [{'id': t.id, 'name': t.name, 'code': t.code, 'is_active': t.state == 'active'} for t in terms],
            'active_term_id': active_term.id if active_term else False,
            'active_term_name': active_term.name if active_term else 'All Terms',
            'kpis': {
                'total_students': total_students_count,
                'active_enrollments': active_enrollments_count,
                'faculty_count': faculty_count,
                'active_sections': active_sections_count,
                'avg_gpa': avg_gpa,
                'avg_attendance': avg_attendance,
                'total_invoiced': total_invoiced,
                'total_collected': total_collected,
                'total_receivable': total_receivable,
                'collection_rate': collection_rate,
            },
            'fee_velocity': {
                'collected': total_collected,
                'pending': pending_amount,
                'overdue': overdue_amount,
                'collected_pct': collection_rate,
                'pending_pct': round(pending_amount / total_invoiced * 100, 1) if total_invoiced else 0,
                'overdue_pct': round(overdue_amount / total_invoiced * 100, 1) if total_invoiced else 0,
            },
            'departments': dept_data,
            'recent_students': recent_students,
            'alerts': alerts,
        }
