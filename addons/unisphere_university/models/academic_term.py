# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class UnisphereAcademicTerm(models.Model):
    _name = 'unisphere.academic.term'
    _description = 'Academic Term / Semester'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date desc, name asc'

    name = fields.Char(
        string='Term Name',
        required=True,
        tracking=True,
        help='Display name of the academic semester (e.g. Fall 2024)'
    )
    code = fields.Char(
        string='Term Code',
        required=True,
        tracking=True,
        help='Short unique code (e.g. F24, S25)'
    )
    start_date = fields.Date(
        string='Start Date',
        required=True,
        tracking=True
    )
    end_date = fields.Date(
        string='End Date',
        required=True,
        tracking=True
    )
    registration_start = fields.Date(
        string='Registration Opens',
        help='Date when course enrollment begins for students.'
    )
    registration_end = fields.Date(
        string='Registration Closes',
        help='Cutoff date for course additions and drops.'
    )
    state = fields.Selection([
        ('draft', 'Draft / Upcoming'),
        ('active', 'Active Semester'),
        ('closed', 'Concluded / Archived')
    ], string='Status', default='draft', required=True, tracking=True)

    active = fields.Boolean(
        string='Active',
        default=True
    )
    section_ids = fields.One2many(
        'unisphere.course.section',
        'term_id',
        string='Scheduled Sections'
    )
    section_count = fields.Integer(
        string='Sections Count',
        compute='_compute_section_count',
        store=True
    )

    _code_unique = models.Constraint(
        'UNIQUE(code)',
        'The Academic Term Code must be unique!'
    )

    @api.depends('section_ids')
    def _compute_section_count(self):
        for record in self:
            record.section_count = len(record.section_ids)

    @api.constrains('start_date', 'end_date', 'registration_start', 'registration_end')
    def _check_term_dates(self):
        for record in self:
            if record.start_date and record.end_date:
                if record.start_date >= record.end_date:
                    raise ValidationError(_("Term Start Date must precede the End Date."))
            if record.registration_start and record.registration_end:
                if record.registration_start >= record.registration_end:
                    raise ValidationError(_("Registration Start Date must precede the Registration End Date."))
            if record.registration_end and record.end_date:
                if record.registration_end > record.end_date:
                    raise ValidationError(_("Registration deadline cannot exceed the term End Date."))

    def action_set_active(self):
        """Set this term as active and transition state"""
        self.ensure_one()
        self.state = 'active'

    def action_set_closed(self):
        """Archive / conclude this semester"""
        self.ensure_one()
        self.state = 'closed'

    def action_set_draft(self):
        """Reset term to draft"""
        self.ensure_one()
        self.state = 'draft'

    def action_view_sections(self):
        """Smart button to open all course sections scheduled in this term"""
        self.ensure_one()
        return {
            'name': _('Sections - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'unisphere.course.section',
            'view_mode': 'list,form',
            'domain': [('term_id', '=', self.id)],
            'context': {'default_term_id': self.id},
        }
