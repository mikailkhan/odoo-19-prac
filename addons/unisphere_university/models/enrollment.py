# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class UnisphereEnrollment(models.Model):
    _name = 'unisphere.enrollment'
    _description = 'Student Course Enrollment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'enrollment_date desc, id desc'
    _rec_name = 'display_name'

    student_id = fields.Many2one(
        'unisphere.student',
        string='Student',
        required=True,
        ondelete='restrict',
        tracking=True
    )
    section_id = fields.Many2one(
        'unisphere.course.section',
        string='Course Section',
        required=True,
        ondelete='restrict',
        tracking=True
    )
    course_id = fields.Many2one(
        related='section_id.course_id',
        string='Course',
        store=True,
        readonly=True
    )
    term_id = fields.Many2one(
        related='section_id.term_id',
        string='Academic Term',
        store=True,
        readonly=True
    )
    department_id = fields.Many2one(
        related='course_id.department_id',
        string='Department',
        store=True,
        readonly=True
    )
    enrollment_date = fields.Date(
        string='Enrollment Date',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    state = fields.Selection([
        ('draft', 'Pending Approval'),
        ('enrolled', 'Confirmed Enrollment'),
        ('dropped', 'Dropped / Withdrawn'),
        ('completed', 'Completed Term')
    ], string='Enrollment Status', default='enrolled', required=True, tracking=True)

    final_grade = fields.Float(
        string='Final Grade Marks',
        default=0.0,
        help='Calculated composite grade marks from continuous assessment.'
    )
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )

    _student_section_unique = models.Constraint(
        'UNIQUE(student_id, section_id)',
        'This student is already registered in this course section!'
    )

    @api.depends('student_id.name', 'section_id.name')
    def _compute_display_name(self):
        for record in self:
            s_name = record.student_id.name if record.student_id else ''
            sec_name = record.section_id.name if record.section_id else ''
            if s_name and sec_name:
                record.display_name = f"{s_name} - {sec_name}"
            else:
                record.display_name = s_name or sec_name or _('New Enrollment')

    @api.constrains('section_id', 'state')
    def _check_section_capacity(self):
        for record in self:
            if record.state == 'enrolled' and record.section_id:
                active_count = self.search_count([
                    ('section_id', '=', record.section_id.id),
                    ('state', '=', 'enrolled'),
                ])
                if active_count > record.section_id.capacity:
                    raise ValidationError(_(
                        "Cannot enroll %(student)s: Course section '%(section)s' has reached maximum capacity of %(cap)d seats!"
                    ) % {
                        'student': record.student_id.name or 'Student',
                        'section': record.section_id.name,
                        'cap': record.section_id.capacity,
                    })

    def action_confirm_enrollment(self):
        self.ensure_one()
        self.state = 'enrolled'

    def action_drop_enrollment(self):
        self.ensure_one()
        self.state = 'dropped'

    def action_complete_enrollment(self):
        self.ensure_one()
        self.state = 'completed'

    def action_reset_draft(self):
        self.ensure_one()
        self.state = 'draft'
