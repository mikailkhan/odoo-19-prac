# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class UnisphereAttendance(models.Model):
    _name = 'unisphere.attendance'
    _description = 'Class Session Attendance Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'class_date desc, section_id asc, student_id asc'
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
    enrollment_id = fields.Many2one(
        'unisphere.enrollment',
        string='Enrollment Record',
        compute='_compute_enrollment_id',
        store=True,
        ondelete='cascade',
        index=True
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
    class_date = fields.Date(
        string='Class Session Date',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    state = fields.Selection([
        ('present', 'Present'),
        ('late', 'Late / Tardy'),
        ('absent', 'Absent / Unexcused'),
    ], string='Attendance Status', default='present', required=True, tracking=True)

    remarks = fields.Char(
        string='Remarks / Notes',
        help='Optional observations (e.g. Excused medical certificate, Left early)'
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

    _attendance_unique = models.Constraint(
        'UNIQUE(student_id, section_id, class_date)',
        'An attendance entry already exists for this student in this course section on this date!'
    )

    @api.depends('student_id', 'section_id')
    def _compute_enrollment_id(self):
        for record in self:
            if record.student_id and record.section_id:
                enr = self.env['unisphere.enrollment'].search([
                    ('student_id', '=', record.student_id.id),
                    ('section_id', '=', record.section_id.id),
                ], limit=1)
                record.enrollment_id = enr.id if enr else False
            else:
                record.enrollment_id = False

    @api.depends('student_id.name', 'section_id.name', 'class_date', 'state')
    def _compute_display_name(self):
        for record in self:
            s_name = record.student_id.name if record.student_id else ''
            sec_name = record.section_id.name if record.section_id else ''
            date_str = str(record.class_date) if record.class_date else ''
            record.display_name = f"{s_name} - {sec_name} ({date_str})"

    @api.constrains('class_date')
    def _check_class_date(self):
        today = fields.Date.today()
        for record in self:
            if record.class_date and record.class_date > today:
                raise ValidationError(_("Attendance cannot be recorded for a future date (%s).") % record.class_date)

    @api.constrains('student_id', 'section_id')
    def _check_student_enrolled(self):
        for record in self:
            if record.student_id and record.section_id:
                # Check active enrollment
                enrolled = self.env['unisphere.enrollment'].search_count([
                    ('student_id', '=', record.student_id.id),
                    ('section_id', '=', record.section_id.id),
                    ('state', '=', 'enrolled'),
                ])
                if not enrolled:
                    raise ValidationError(_(
                        "Student '%(student)s' is not actively enrolled in section '%(section)s'!"
                    ) % {
                        'student': record.student_id.name,
                        'section': record.section_id.name,
                    })
