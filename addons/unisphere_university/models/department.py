# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class UnisphereDepartment(models.Model):
    _name = 'unisphere.department'
    _description = 'Academic Department'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc'

    name = fields.Char(
        string='Department Name',
        required=True,
        tracking=True,
        help='Full name of the department (e.g. Department of Computer Science)'
    )
    code = fields.Char(
        string='Department Code',
        required=True,
        tracking=True,
        help='Unique identifier code (e.g. CS, EE, SE)'
    )
    description = fields.Text(
        string='Description',
        help='Overview, mission, and scope of this academic department.'
    )
    head_of_department_id = fields.Many2one(
        'res.partner',
        string='Head of Department (HoD)',
        tracking=True,
        help='Faculty member or contact serving as Chairperson / HoD.'
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Deactivate to archive this department from current listings.'
    )
    course_ids = fields.One2many(
        'unisphere.course',
        'department_id',
        string='Offered Courses'
    )
    course_count = fields.Integer(
        string='Course Count',
        compute='_compute_course_count',
        store=True
    )

    _code_unique = models.Constraint(
        'UNIQUE(code)',
        'The Department Code must be unique across the university!'
    )

    @api.depends('course_ids')
    def _compute_course_count(self):
        for record in self:
            record.course_count = len(record.course_ids)

    @api.constrains('code')
    def _check_code_format(self):
        for record in self:
            if not record.code or not record.code.strip():
                raise ValidationError(_("Department Code cannot be empty or whitespace."))
            # Normalize to uppercase
            if record.code != record.code.upper():
                record.code = record.code.upper()

    def action_view_courses(self):
        """Action for smart button to view all courses belonging to this department"""
        self.ensure_one()
        return {
            'name': _('Courses - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'unisphere.course',
            'view_mode': 'list,form',
            'domain': [('department_id', '=', self.id)],
            'context': {'default_department_id': self.id},
        }
