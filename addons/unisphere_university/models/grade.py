# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


def get_letter_grade_and_point(pct):
    """Standard Institutional Grading Scale for Northstar University of Technology"""
    if pct >= 85.0:
        return 'A', 4.00
    elif pct >= 80.0:
        return 'A-', 3.70
    elif pct >= 75.0:
        return 'B+', 3.30
    elif pct >= 70.0:
        return 'B', 3.00
    elif pct >= 65.0:
        return 'B-', 2.70
    elif pct >= 60.0:
        return 'C+', 2.30
    elif pct >= 55.0:
        return 'C', 2.00
    elif pct >= 50.0:
        return 'D', 1.00
    else:
        return 'F', 0.00


class UnisphereGrade(models.Model):
    _name = 'unisphere.grade'
    _description = 'Student Assessment Grade Entry'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'assessment_id desc, marks_obtained desc'
    _rec_name = 'display_name'

    assessment_id = fields.Many2one(
        'unisphere.assessment',
        string='Assessment',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    student_id = fields.Many2one(
        'unisphere.student',
        string='Student',
        required=True,
        ondelete='restrict',
        tracking=True
    )
    section_id = fields.Many2one(
        related='assessment_id.section_id',
        string='Course Section',
        store=True,
        readonly=True
    )
    course_id = fields.Many2one(
        related='assessment_id.course_id',
        string='Course',
        store=True,
        readonly=True
    )
    term_id = fields.Many2one(
        related='assessment_id.term_id',
        string='Academic Term',
        store=True,
        readonly=True
    )
    department_id = fields.Many2one(
        related='assessment_id.department_id',
        string='Department',
        store=True,
        readonly=True
    )
    enrollment_id = fields.Many2one(
        'unisphere.enrollment',
        string='Enrollment Record',
        compute='_compute_enrollment_id',
        store=True,
        ondelete='cascade',
        index=True
    )
    max_marks = fields.Float(
        related='assessment_id.max_marks',
        string='Max Marks',
        store=True,
        readonly=True
    )
    marks_obtained = fields.Float(
        string='Marks Obtained',
        required=True,
        default=0.0,
        tracking=True
    )
    percentage = fields.Float(
        string='Score (%)',
        compute='_compute_score_metrics',
        store=True,
        digits=(5, 2)
    )
    letter_grade = fields.Char(
        string='Letter Grade',
        compute='_compute_score_metrics',
        store=True
    )
    grade_point = fields.Float(
        string='Grade Point',
        compute='_compute_score_metrics',
        store=True,
        digits=(3, 2)
    )
    remarks = fields.Char(
        string='Feedback / Observations',
        help='Faculty observations or comments on student performance.'
    )
    state = fields.Selection([
        ('draft', 'Draft Entry'),
        ('graded', 'Graded'),
        ('published', 'Published')
    ], string='Status', default='graded', required=True, tracking=True)

    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )

    _student_assessment_unique = models.Constraint(
        'UNIQUE(assessment_id, student_id)',
        'A grade entry already exists for this student on this assessment!'
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

    @api.depends('marks_obtained', 'max_marks')
    def _compute_score_metrics(self):
        for record in self:
            if record.max_marks > 0:
                pct = round((record.marks_obtained / record.max_marks) * 100.0, 2)
                letter, gp = get_letter_grade_and_point(pct)
                record.percentage = pct
                record.letter_grade = letter
                record.grade_point = gp
            else:
                record.percentage = 0.0
                record.letter_grade = 'F'
                record.grade_point = 0.0

    @api.depends('student_id.name', 'assessment_id.name', 'marks_obtained', 'max_marks')
    def _compute_display_name(self):
        for record in self:
            s_name = record.student_id.name if record.student_id else ''
            a_name = record.assessment_id.name if record.assessment_id else ''
            score_str = f"{record.marks_obtained:g}/{record.max_marks:g}" if record.max_marks else ''
            record.display_name = f"{s_name} - {a_name} ({score_str})"

    @api.constrains('marks_obtained', 'assessment_id')
    def _check_marks_obtained(self):
        for record in self:
            if record.marks_obtained < 0:
                raise ValidationError(_("Marks obtained cannot be negative."))
            if record.assessment_id and record.marks_obtained > record.assessment_id.max_marks:
                raise ValidationError(_(
                    "Marks obtained (%(obtained)s) cannot exceed assessment maximum marks (%(max)s)!"
                ) % {
                    'obtained': record.marks_obtained,
                    'max': record.assessment_id.max_marks,
                })

    @api.constrains('student_id', 'assessment_id')
    def _check_student_enrolled(self):
        for record in self:
            if record.student_id and record.assessment_id and record.assessment_id.section_id:
                enrolled = self.env['unisphere.enrollment'].search_count([
                    ('student_id', '=', record.student_id.id),
                    ('section_id', '=', record.assessment_id.section_id.id),
                    ('state', '=', 'enrolled'),
                ])
                if not enrolled:
                    raise ValidationError(_(
                        "Student '%(student)s' is not actively enrolled in section '%(section)s'!"
                    ) % {
                        'student': record.student_id.name,
                        'section': record.assessment_id.section_id.name,
                    })

    def action_publish_grade(self):
        self.ensure_one()
        self.state = 'published'

    def action_reset_draft(self):
        self.ensure_one()
        self.state = 'draft'
