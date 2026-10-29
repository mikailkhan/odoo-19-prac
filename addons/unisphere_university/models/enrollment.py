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

    grade_ids = fields.One2many(
        'unisphere.grade',
        'enrollment_id',
        string='Grades'
    )
    final_grade = fields.Float(
        string='Final Grade Marks',
        compute='_compute_final_grade_metrics',
        store=True,
        digits=(5, 2),
        help='Calculated composite grade marks from continuous assessment weightages.'
    )
    letter_grade = fields.Char(
        string='Letter Grade',
        compute='_compute_final_grade_metrics',
        store=True,
        help='Letter grade according to official university scale (A, B+, etc.)'
    )
    grade_point = fields.Float(
        string='Grade Point (4.0)',
        compute='_compute_final_grade_metrics',
        store=True,
        digits=(3, 2),
        help='Grade point contribution for GPA calculations.'
    )
    is_passed = fields.Boolean(
        string='Course Passed',
        compute='_compute_final_grade_metrics',
        store=True
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
    attendance_ids = fields.One2many(
        'unisphere.attendance',
        'enrollment_id',
        string='Attendance Records'
    )
    total_sessions = fields.Integer(
        string='Total Sessions',
        compute='_compute_attendance_stats',
        store=True
    )
    attended_sessions = fields.Integer(
        string='Attended Sessions',
        compute='_compute_attendance_stats',
        store=True,
        help='Sessions marked as Present or Late'
    )
    absent_sessions = fields.Integer(
        string='Absent Sessions',
        compute='_compute_attendance_stats',
        store=True
    )
    attendance_rate = fields.Float(
        string='Attendance Rate (%)',
        compute='_compute_attendance_stats',
        store=True,
        digits=(5, 2),
        help='Percentage of sessions attended (Present + Late)'
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

    @api.depends('attendance_ids.state')
    def _compute_attendance_stats(self):
        for record in self:
            total = len(record.attendance_ids)
            attended = len(record.attendance_ids.filtered(lambda a: a.state in ('present', 'late')))
            absent = len(record.attendance_ids.filtered(lambda a: a.state == 'absent'))
            record.total_sessions = total
            record.attended_sessions = attended
            record.absent_sessions = absent
            record.attendance_rate = round((attended / total * 100.0), 2) if total > 0 else 100.0

    @api.depends('grade_ids.marks_obtained', 'grade_ids.max_marks', 'grade_ids.assessment_id.weightage', 'grade_ids.state')
    def _compute_final_grade_metrics(self):
        from .grade import get_letter_grade_and_point
        for record in self:
            valid_grades = record.grade_ids.filtered(lambda g: g.state in ('graded', 'published'))
            if not valid_grades:
                record.final_grade = 0.0
                record.letter_grade = 'N/A'
                record.grade_point = 0.00
                record.is_passed = False
                continue

            total_weighted_score = 0.0
            evaluated_weightage = 0.0
            for g in valid_grades:
                if g.max_marks > 0 and g.assessment_id:
                    total_weighted_score += (g.marks_obtained / g.max_marks) * g.assessment_id.weightage
                    evaluated_weightage += g.assessment_id.weightage

            if evaluated_weightage > 0:
                final_pct = round((total_weighted_score / evaluated_weightage) * 100.0, 2)
            else:
                final_pct = 0.0

            letter, gp = get_letter_grade_and_point(final_pct)
            record.final_grade = final_pct
            record.letter_grade = letter
            record.grade_point = gp
            record.is_passed = (letter != 'F' and final_pct >= 50.0)

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
