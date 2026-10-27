# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class UnisphereStudent(models.Model):
    _name = 'unisphere.student'
    _description = 'University Student Profile'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'student_id asc, name asc'
    _rec_name = 'display_name'

    partner_id = fields.Many2one(
        'res.partner',
        string='Contact Record',
        required=True,
        ondelete='restrict',
        tracking=True,
        help='Linked Odoo contact holding core identity, address, and avatar.'
    )
    name = fields.Char(
        related='partner_id.name',
        string='Student Name',
        store=True,
        readonly=False,
        tracking=True
    )
    student_id = fields.Char(
        string='Student ID / Reg No',
        required=True,
        tracking=True,
        help='Unique matriculation number (e.g. NUT-2024-CS-0142)'
    )
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    email = fields.Char(
        related='partner_id.email',
        string='University / Personal Email',
        readonly=False
    )
    phone = fields.Char(
        related='partner_id.phone',
        string='Contact Phone',
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
        string='Portal User Account',
        tracking=True,
        help='Authentication account for self-service Student Portal access.'
    )
    department_id = fields.Many2one(
        'unisphere.department',
        string='Academic Department',
        required=True,
        tracking=True
    )
    program = fields.Selection([
        ('bs_cs', 'BS Computer Science'),
        ('bs_se', 'BS Software Engineering'),
        ('bs_ee', 'BS Electrical Engineering'),
        ('bs_ai', 'BS Artificial Intelligence'),
        ('bba', 'Bachelor of Business Administration'),
        ('ms_cs', 'MS Computer Science'),
    ], string='Degree Program', required=True, default='bs_cs', tracking=True)

    admission_date = fields.Date(
        string='Admission Date',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    current_term_id = fields.Many2one(
        'unisphere.academic.term',
        string='Current Academic Term',
        tracking=True
    )
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], string='Gender', default='male')

    date_of_birth = fields.Date(string='Date of Birth')

    blood_group = fields.Selection([
        ('a_pos', 'A+'),
        ('a_neg', 'A-'),
        ('b_pos', 'B+'),
        ('b_neg', 'B-'),
        ('ab_pos', 'AB+'),
        ('ab_neg', 'AB-'),
        ('o_pos', 'O+'),
        ('o_neg', 'O-'),
    ], string='Blood Group')

    state = fields.Selection([
        ('draft', 'Admitted (Pending Enrollment)'),
        ('enrolled', 'Active Student'),
        ('suspended', 'Suspended'),
        ('graduated', 'Graduated'),
        ('withdrawn', 'Withdrawn')
    ], string='Status', default='enrolled', required=True, tracking=True)

    active = fields.Boolean(
        string='Active',
        default=True
    )

    _student_id_unique = models.Constraint(
        'UNIQUE(student_id)',
        'The Student Registration ID must be unique across the entire institution!'
    )

    @api.depends('student_id', 'name')
    def _compute_display_name(self):
        for record in self:
            if record.student_id and record.name:
                record.display_name = f"[{record.student_id}] {record.name}"
            elif record.name:
                record.display_name = record.name
            else:
                record.display_name = record.student_id or ''

    @api.constrains('student_id')
    def _check_student_id_format(self):
        for record in self:
            if not record.student_id or not record.student_id.strip():
                raise ValidationError(_("Student ID cannot be empty or blank."))

    def action_set_enrolled(self):
        self.ensure_one()
        self.state = 'enrolled'

    def action_set_suspended(self):
        self.ensure_one()
        self.state = 'suspended'

    def action_set_graduated(self):
        self.ensure_one()
        self.state = 'graduated'
