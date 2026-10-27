# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class UnisphereCourseSection(models.Model):
    _name = 'unisphere.course.section'
    _description = 'Course Section Offering'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'term_id desc, course_id asc, section_code asc'

    name = fields.Char(
        string='Section Name',
        compute='_compute_name',
        store=True,
        tracking=True
    )
    course_id = fields.Many2one(
        'unisphere.course',
        string='Course',
        required=True,
        ondelete='restrict',
        tracking=True
    )
    term_id = fields.Many2one(
        'unisphere.academic.term',
        string='Academic Term',
        required=True,
        ondelete='restrict',
        tracking=True
    )
    section_code = fields.Char(
        string='Section Code',
        required=True,
        default='A',
        tracking=True,
        help='Section group identifier (e.g. CS-1A, Section 1)'
    )
    department_id = fields.Many2one(
        related='course_id.department_id',
        string='Department',
        store=True,
        readonly=True
    )
    instructor_id = fields.Many2one(
        'unisphere.faculty',
        string='Primary Instructor / Faculty',
        tracking=True,
        help='Assigned faculty member for lectures and grading.'
    )
    classroom = fields.Char(
        string='Classroom / Hall',
        help='Assigned physical or virtual hall (e.g. Hall B-104, Lab 3)'
    )
    schedule = fields.Char(
        string='Class Schedule',
        help='Weekly time slots (e.g. Mon / Wed 09:00 - 10:30)'
    )
    capacity = fields.Integer(
        string='Total Capacity',
        required=True,
        default=40,
        tracking=True,
        help='Maximum number of students permitted to enroll.'
    )
    enrollment_ids = fields.One2many(
        'unisphere.enrollment',
        'section_id',
        string='Roster Records'
    )
    enrolled_count = fields.Integer(
        string='Enrolled Students',
        compute='_compute_enrolled_count',
        store=True,
        help='Current confirmed student enrollments.'
    )
    seats_available = fields.Integer(
        string='Available Seats',
        compute='_compute_seats_available',
        store=True
    )
    state = fields.Selection([
        ('draft', 'Draft Setup'),
        ('open', 'Open for Registration'),
        ('closed', 'Registration Closed'),
        ('completed', 'Term Completed')
    ], string='Status', default='open', required=True, tracking=True)

    _section_term_unique = models.Constraint(
        'UNIQUE(course_id, term_id, section_code)',
        'A section with this code already exists for this course in the selected academic term!'
    )

    @api.depends('course_id.code', 'section_code', 'term_id.code')
    def _compute_name(self):
        for record in self:
            c_code = record.course_id.code if record.course_id else ''
            s_code = record.section_code or ''
            t_code = record.term_id.code if record.term_id else ''
            if c_code and s_code and t_code:
                record.name = f"{c_code} - {s_code} ({t_code})"
            elif c_code and s_code:
                record.name = f"{c_code} - {s_code}"
            else:
                record.name = s_code or _('New Section')

    @api.depends('enrollment_ids.state')
    def _compute_enrolled_count(self):
        for record in self:
            record.enrolled_count = len(record.enrollment_ids.filtered(lambda e: e.state == 'enrolled'))

    @api.depends('capacity', 'enrolled_count')
    def _compute_seats_available(self):
        for record in self:
            record.seats_available = max(0, record.capacity - record.enrolled_count)

    def action_view_roster(self):
        """Smart button action to view student roster for this section"""
        self.ensure_one()
        return {
            'name': _('Class Roster - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'unisphere.enrollment',
            'view_mode': 'list,form',
            'domain': [('section_id', '=', self.id)],
            'context': {'default_section_id': self.id},
        }

    @api.constrains('capacity')
    def _check_capacity(self):
        for record in self:
            if record.capacity <= 0:
                raise ValidationError(_("Section capacity must be greater than zero."))

    def action_open_registration(self):
        self.ensure_one()
        self.state = 'open'

    def action_close_registration(self):
        self.ensure_one()
        self.state = 'closed'

    def action_mark_completed(self):
        self.ensure_one()
        self.state = 'completed'
