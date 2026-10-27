# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class UnisphereFaculty(models.Model):
    _name = 'unisphere.faculty'
    _description = 'University Faculty Member'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc'
    _rec_name = 'display_name'

    partner_id = fields.Many2one(
        'res.partner',
        string='Contact Record',
        required=True,
        ondelete='restrict',
        tracking=True,
        help='Linked Odoo contact holding core identity and avatar.'
    )
    name = fields.Char(
        related='partner_id.name',
        string='Faculty Name',
        store=True,
        readonly=False,
        tracking=True
    )
    faculty_id = fields.Char(
        string='Faculty ID / Staff Code',
        required=True,
        tracking=True,
        help='Unique staff employee identifier (e.g. NUT-FAC-0089)'
    )
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    email = fields.Char(
        related='partner_id.email',
        string='Institutional Email',
        readonly=False
    )
    phone = fields.Char(
        related='partner_id.phone',
        string='Phone Extension',
        readonly=False
    )
    image_1920 = fields.Image(
        related='partner_id.image_1920',
        string='Profile Picture',
        readonly=False
    )
    avatar_128 = fields.Image(
        related='partner_id.avatar_128',
        string='Avatar'
    )
    user_id = fields.Many2one(
        'res.users',
        string='System User Account',
        tracking=True,
        help='Internal login account enabling backend gradebook and attendance entry.'
    )
    department_id = fields.Many2one(
        'unisphere.department',
        string='Academic Department',
        required=True,
        tracking=True
    )
    designation = fields.Selection([
        ('professor', 'Professor'),
        ('assoc_prof', 'Associate Professor'),
        ('asst_prof', 'Assistant Professor'),
        ('lecturer', 'Lecturer'),
        ('adjunct', 'Adjunct Fellow'),
    ], string='Designation', required=True, default='lecturer', tracking=True)

    qualification = fields.Char(
        string='Highest Qualification',
        help='e.g. Ph.D. in Computer Science (Stanford), M.S. Software Engineering'
    )
    specialization = fields.Char(
        string='Area of Specialization',
        help='e.g. Distributed Systems, Machine Learning, Embedded Hardware'
    )
    section_ids = fields.One2many(
        'unisphere.course.section',
        'instructor_id',
        string='Assigned Course Sections'
    )
    section_count = fields.Integer(
        string='Teaching Sections Count',
        compute='_compute_section_count',
        store=True
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )

    _faculty_id_unique = models.Constraint(
        'UNIQUE(faculty_id)',
        'The Faculty Identifier must be unique across the university!'
    )

    @api.depends('faculty_id', 'name')
    def _compute_display_name(self):
        for record in self:
            if record.faculty_id and record.name:
                record.display_name = f"[{record.faculty_id}] {record.name}"
            elif record.name:
                record.display_name = record.name
            else:
                record.display_name = record.faculty_id or ''

    @api.depends('section_ids')
    def _compute_section_count(self):
        for record in self:
            record.section_count = len(record.section_ids)

    def action_view_sections(self):
        """Smart button to open all course sections taught by this faculty member"""
        self.ensure_one()
        return {
            'name': _('Sections Taught by %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'unisphere.course.section',
            'view_mode': 'list,form',
            'domain': [('instructor_id', '=', self.id)],
            'context': {'default_instructor_id': self.id},
        }
