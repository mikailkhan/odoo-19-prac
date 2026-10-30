# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.addons.web.controllers.home import Home as WebHome
from odoo.addons.web.controllers.utils import is_user_internal


class UniSphereHome(WebHome):

    @http.route(['/', '/home'], type='http', auth="public", website=True, sitemap=True)
    def index(self, *args, **kw):
        """
        Public Institutional Homepage for Northstar University of Technology (NUT).
        Provides university overview, academic department catalog, live stats,
        and 1-click persona logins for students, faculty, and administrators.
        """
        # Ensure company branding
        company = request.env['res.company'].sudo().search([], limit=1)
        if company and company.name == 'My Company':
            company.write({'name': 'Northstar University of Technology'})

        Department = request.env['unisphere.department'].sudo()
        Term = request.env['unisphere.academic.term'].sudo()
        Student = request.env['unisphere.student'].sudo()
        Faculty = request.env['unisphere.faculty'].sudo()
        Course = request.env['unisphere.course'].sudo()
        Section = request.env['unisphere.course.section'].sudo()

        departments = Department.search([], order='code asc')
        active_term = Term.search([('state', '=', 'active')], limit=1)
        if not active_term:
            active_term = Term.search([], order='id desc', limit=1)

        total_students = Student.search_count([('state', '=', 'enrolled')])
        total_faculty = Faculty.search_count([('active', '=', True)])
        total_courses = Course.search_count([('active', '=', True)])
        total_sections = Section.search_count([('state', 'in', ['open', 'in_progress'])])

        # Current session state
        user = request.env.user
        is_logged_in = not user._is_public()
        is_admin = user.has_group('unisphere_university.group_unisphere_admin')
        is_student = user.has_group('unisphere_university.group_unisphere_student')
        student_record = None
        if is_student:
            student_record = Student.search([('partner_id', '=', user.partner_id.id)], limit=1)

        values = {
            'company': company,
            'departments': departments,
            'active_term': active_term,
            'total_students': total_students,
            'total_faculty': total_faculty,
            'total_courses': total_courses,
            'total_sections': total_sections,
            'is_logged_in': is_logged_in,
            'is_admin': is_admin,
            'is_student': is_student,
            'student_record': student_record,
            'current_user': user,
        }
        return request.render('unisphere_university.homepage', values)
