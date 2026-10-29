# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class UnisphereAssessment(models.Model):
    _name = 'unisphere.assessment'
    _description = 'Course Assessment Component'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'due_date desc, id desc'
    _rec_name = 'display_name'

    name = fields.Char(
        string='Assessment Title',
        required=True,
        tracking=True,
        help='Title of the assessment (e.g. Midterm Exam, Quiz 1, Project Milestone 1)'
    )
    section_id = fields.Many2one(
        'unisphere.course.section',
        string='Course Section',
        required=True,
        ondelete='cascade',
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
    assessment_type = fields.Selection([
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment / Homework'),
        ('midterm', 'Midterm Examination'),
        ('project', 'Term Project'),
        ('final', 'Final Examination'),
        ('practical', 'Lab Practical')
    ], string='Assessment Type', required=True, default='assignment', tracking=True)

    max_marks = fields.Float(
        string='Maximum Marks / Total Points',
        required=True,
        default=100.0,
        tracking=True,
        help='Total maximum points attainable on this evaluation.'
    )
    weightage = fields.Float(
        string='Course Weightage (%)',
        required=True,
        default=20.0,
        tracking=True,
        help='Percentage weight contributed to final course grade (e.g. 20% for Midterm).'
    )
    due_date = fields.Date(
        string='Due Date / Exam Date',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    grade_ids = fields.One2many(
        'unisphere.grade',
        'assessment_id',
        string='Student Grades'
    )
    graded_count = fields.Integer(
        string='Graded Students',
        compute='_compute_grade_metrics',
        store=True
    )
    average_score = fields.Float(
        string='Class Average (%)',
        compute='_compute_grade_metrics',
        store=True,
        digits=(5, 2)
    )
    state = fields.Selection([
        ('draft', 'Draft Plan'),
        ('announced', 'Announced to Students'),
        ('grading', 'Grading in Progress'),
        ('published', 'Grades Published')
    ], string='Status', default='draft', required=True, tracking=True)

    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )

    _section_name_unique = models.Constraint(
        'UNIQUE(section_id, name)',
        'An assessment with this title already exists in this course section!'
    )

    @api.depends('name', 'section_id.name', 'assessment_type')
    def _compute_display_name(self):
        for record in self:
            sec_name = record.section_id.name if record.section_id else ''
            if sec_name and record.name:
                record.display_name = f"{record.name} - {sec_name}"
            else:
                record.display_name = record.name or _('New Assessment')

    @api.depends('grade_ids.marks_obtained', 'grade_ids.state', 'max_marks')
    def _compute_grade_metrics(self):
        for record in self:
            grades = record.grade_ids.filtered(lambda g: g.state in ('graded', 'published'))
            record.graded_count = len(grades)
            if grades and record.max_marks > 0:
                percentages = [(g.marks_obtained / record.max_marks) * 100.0 for g in grades]
                record.average_score = round(sum(percentages) / len(percentages), 2)
            else:
                record.average_score = 0.0

    @api.constrains('max_marks', 'weightage')
    def _check_marks_and_weightage(self):
        for record in self:
            if record.max_marks <= 0:
                raise ValidationError(_("Maximum marks must be strictly greater than 0."))
            if record.weightage <= 0 or record.weightage > 100:
                raise ValidationError(_("Assessment weightage must be between 1% and 100%."))

    @api.constrains('section_id', 'weightage')
    def _check_total_section_weightage(self):
        for record in self:
            if record.section_id:
                assessments = self.search([
                    ('section_id', '=', record.section_id.id),
                    ('id', '!=', record.id)
                ])
                total_weightage = sum(a.weightage for a in assessments) + record.weightage
                if total_weightage > 100.001:  # small epsilon for floating point
                    raise ValidationError(_(
                        "The total assessment weightage for section '%(sec)s' would exceed 100%% (Current total: %(tot).1f%%)!"
                    ) % {
                        'sec': record.section_id.name,
                        'tot': total_weightage,
                    })

    def action_announce(self):
        self.ensure_one()
        self.state = 'announced'

    def action_start_grading(self):
        self.ensure_one()
        self.state = 'grading'

    def action_publish(self):
        self.ensure_one()
        self.state = 'published'
        # Mark all related grade lines as published
        self.grade_ids.write({'state': 'published'})

    def action_reset_draft(self):
        self.ensure_one()
        self.state = 'draft'

    def action_quick_grade(self):
        """Open quick grading wizard for all students in this section"""
        self.ensure_one()
        return {
            'name': _('Grade Assessment: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'unisphere.grade.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_assessment_id': self.id,
            },
        }
