# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class UnisphereCourse(models.Model):
    _name = 'unisphere.course'
    _description = 'Academic Course'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'code asc, name asc'
    _rec_name = 'display_name'

    name = fields.Char(
        string='Course Title',
        required=True,
        tracking=True,
        help='Full title of the course (e.g. Introduction to Computing)'
    )
    code = fields.Char(
        string='Course Code',
        required=True,
        tracking=True,
        help='Catalog code (e.g. CS101, SE301)'
    )
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    department_id = fields.Many2one(
        'unisphere.department',
        string='Department',
        required=True,
        ondelete='restrict',
        tracking=True,
        help='Academic department offering this course.'
    )
    credit_hours = fields.Integer(
        string='Credit Hours',
        required=True,
        default=3,
        tracking=True,
        help='Number of academic credit hours (1 to 6).'
    )
    description = fields.Text(
        string='Syllabus & Course Description',
        help='Summary of course objectives, syllabus, and learning outcomes.'
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )
    section_ids = fields.One2many(
        'unisphere.course.section',
        'course_id',
        string='Course Offerings / Sections'
    )
    section_count = fields.Integer(
        string='Offerings Count',
        compute='_compute_section_count',
        store=True
    )

    _code_unique = models.Constraint(
        'UNIQUE(code)',
        'The Course Code must be unique across the university!'
    )

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for record in self:
            if record.code and record.name:
                record.display_name = f"[{record.code}] {record.name}"
            elif record.name:
                record.display_name = record.name
            else:
                record.display_name = record.code or ''

    @api.depends('section_ids')
    def _compute_section_count(self):
        for record in self:
            record.section_count = len(record.section_ids)

    @api.constrains('credit_hours')
    def _check_credit_hours(self):
        for record in self:
            if record.credit_hours < 1 or record.credit_hours > 6:
                raise ValidationError(_("Credit hours must be between 1 and 6."))

    def action_view_sections(self):
        """Smart button to open all sections offering this course"""
        self.ensure_one()
        return {
            'name': _('Sections - %s') % self.display_name,
            'type': 'ir.actions.act_window',
            'res_model': 'unisphere.course.section',
            'view_mode': 'list,form',
            'domain': [('course_id', '=', self.id)],
            'context': {'default_course_id': self.id},
        }
