# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from werkzeug.exceptions import Forbidden, NotFound


class UniSphereStudentPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        """Inject UniSphere student counters into the native /my home portal page."""
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        student = request.env['unisphere.student'].search([('partner_id', '=', partner.id)], limit=1)

        if not student and request.env.user.has_group('unisphere_university.group_unisphere_admin'):
            # Admin preview fallback
            student = request.env['unisphere.student'].search([], limit=1)

        if 'unisphere_courses_count' in counters:
            values['unisphere_courses_count'] = len(student.enrollment_ids.filtered(lambda e: e.state == 'enrolled')) if student else 0

        if 'unisphere_fees_count' in counters:
            values['unisphere_fees_count'] = request.env['unisphere.fee'].search_count([('student_id', '=', student.id)]) if student else 0

        return values

    def _get_portal_student(self):
        """Retrieve current logged-in student profile or admin preview."""
        partner = request.env.user.partner_id
        student = request.env['unisphere.student'].search([('partner_id', '=', partner.id)], limit=1)
        if not student:
            if request.env.user.has_group('unisphere_university.group_unisphere_admin'):
                # Admin fallback: preview as first enrolled student
                student = request.env['unisphere.student'].search([('state', '=', 'enrolled')], limit=1)
        return student

    # -------------------------------------------------------------------------
    # 1. Main Student Portal Dashboard (/my/unisphere)
    # -------------------------------------------------------------------------
    @http.route(['/my/unisphere', '/my/unisphere/home'], type='http', auth='user', website=True)
    def portal_my_unisphere(self, **kw):
        student = self._get_portal_student()
        if not student:
            return request.render('unisphere_university.portal_no_student_profile', {})

        # Active Enrollments
        active_enrollments = student.enrollment_ids.filtered(lambda e: e.state == 'enrolled')

        # Recent Published Grades across all courses
        recent_grades = request.env['unisphere.grade'].search([
            ('student_id', '=', student.id),
            ('assessment_id.state', '=', 'published')
        ], order='id desc', limit=6)

        # Financial Standing
        student_fees = request.env['unisphere.fee'].search([('student_id', '=', student.id)])
        total_invoiced = sum(f.amount_due for f in student_fees)
        total_paid = sum(f.amount_paid for f in student_fees)
        total_balance_due = sum(f.balance_due for f in student_fees)

        # Attendance Counts
        attendance_total_count = student.attendance_count
        attendance_present_count = len(student.attendance_ids.filtered(lambda a: a.state in ('present', 'late')))

        values = {
            'student': student,
            'page_name': 'unisphere_home',
            'active_enrollments': active_enrollments,
            'recent_grades': recent_grades,
            'attendance_total_count': attendance_total_count,
            'attendance_present_count': attendance_present_count,
            'total_invoiced': total_invoiced,
            'total_paid': total_paid,
            'total_balance_due': total_balance_due,
            'is_admin_preview': not bool(student.partner_id == request.env.user.partner_id),
        }
        return request.render('unisphere_university.portal_my_dashboard', values)

    # -------------------------------------------------------------------------
    # 2. Course Section Details (/my/unisphere/courses/<id>)
    # -------------------------------------------------------------------------
    @http.route(['/my/unisphere/courses/<int:section_id>'], type='http', auth='user', website=True)
    def portal_my_course_section(self, section_id, **kw):
        student = self._get_portal_student()
        if not student:
            return request.render('unisphere_university.portal_no_student_profile', {})

        section = request.env['unisphere.course.section'].browse(section_id)
        if not section.exists():
            raise NotFound()

        # Strict Security Isolation: Check enrollment
        is_admin = request.env.user.has_group('unisphere_university.group_unisphere_admin')
        enrollment = request.env['unisphere.enrollment'].search([
            ('student_id', '=', student.id),
            ('section_id', '=', section_id),
            ('state', '=', 'enrolled')
        ], limit=1)

        if not enrollment and not is_admin:
            raise Forbidden(_("Access Denied: You are not enrolled in this course section."))

        # Attendance breakdown for this specific section
        attendances = request.env['unisphere.attendance'].search([
            ('student_id', '=', student.id),
            ('section_id', '=', section_id)
        ], order='class_date desc')

        total_sessions = len(attendances)
        present_sessions = len(attendances.filtered(lambda a: a.state in ('present', 'late')))
        attendance_percentage = round((present_sessions / total_sessions * 100), 1) if total_sessions else 100.0

        # Published continuous assessment grades
        grades = request.env['unisphere.grade'].search([
            ('student_id', '=', student.id),
            ('assessment_id.section_id', '=', section_id),
            ('assessment_id.state', '=', 'published')
        ], order='id desc')

        values = {
            'student': student,
            'section': section,
            'enrollment': enrollment,
            'attendances': attendances,
            'total_sessions': total_sessions,
            'present_sessions': present_sessions,
            'attendance_percentage': attendance_percentage,
            'grades': grades,
            'page_name': 'unisphere_course_detail',
            'is_admin_preview': not bool(student.partner_id == request.env.user.partner_id),
        }
        return request.render('unisphere_university.portal_course_section_detail', values)

    # -------------------------------------------------------------------------
    # 3. Student Fee Ledger (/my/unisphere/fees)
    # -------------------------------------------------------------------------
    @http.route(['/my/unisphere/fees'], type='http', auth='user', website=True)
    def portal_my_fees(self, **kw):
        student = self._get_portal_student()
        if not student:
            return request.render('unisphere_university.portal_no_student_profile', {})

        fees = request.env['unisphere.fee'].search([
            ('student_id', '=', student.id)
        ], order='issue_date desc')

        total_invoiced = sum(f.amount_due for f in fees)
        total_paid = sum(f.amount_paid for f in fees)
        total_balance_due = sum(f.balance_due for f in fees)

        values = {
            'student': student,
            'fees': fees,
            'total_invoiced': total_invoiced,
            'total_paid': total_paid,
            'total_balance_due': total_balance_due,
            'page_name': 'unisphere_fees',
            'is_admin_preview': not bool(student.partner_id == request.env.user.partner_id),
        }
        return request.render('unisphere_university.portal_my_fees', values)
