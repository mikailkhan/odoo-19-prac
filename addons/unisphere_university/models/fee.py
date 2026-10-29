# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class UnisphereFee(models.Model):
    _name = 'unisphere.fee'
    _description = 'Student Tuition & Fee Challan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'due_date desc, id desc'
    _rec_name = 'display_name'

    challan_number = fields.Char(
        string='Challan / Voucher #',
        required=True,
        readonly=True,
        copy=False,
        default=lambda self: _('New'),
        tracking=True
    )
    student_id = fields.Many2one(
        'unisphere.student',
        string='Student',
        required=True,
        ondelete='restrict',
        tracking=True
    )
    department_id = fields.Many2one(
        related='student_id.department_id',
        string='Department',
        store=True,
        readonly=True
    )
    term_id = fields.Many2one(
        'unisphere.academic.term',
        string='Academic Term',
        required=True,
        ondelete='restrict',
        tracking=True
    )
    fee_type = fields.Selection([
        ('tuition', 'Tuition Fee (Per Term)'),
        ('admission', 'Admission & Registration Fee'),
        ('lab', 'Laboratory & Technology Fee'),
        ('library', 'Library & Resources Fee'),
        ('exam', 'Examination Fee'),
        ('hostel', 'Hostel & Accommodation Fee'),
        ('other', 'Miscellaneous Institutional Fee')
    ], string='Fee Classification', default='tuition', required=True, tracking=True)

    issue_date = fields.Date(
        string='Issue Date',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    due_date = fields.Date(
        string='Due Date',
        required=True,
        tracking=True
    )
    amount_due = fields.Float(
        string='Amount Invoiced ($)',
        required=True,
        default=0.0,
        tracking=True,
        digits=(10, 2)
    )
    amount_paid = fields.Float(
        string='Amount Paid ($)',
        required=True,
        default=0.0,
        tracking=True,
        digits=(10, 2)
    )
    balance_due = fields.Float(
        string='Balance Due ($)',
        compute='_compute_balance_due',
        store=True,
        digits=(10, 2)
    )
    state = fields.Selection([
        ('draft', 'Draft Setup'),
        ('posted', 'Issued / Unpaid'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid in Full'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled')
    ], string='Billing Status', default='draft', tracking=True)

    payment_method = fields.Selection([
        ('bank_transfer', 'Bank Deposit / 1Link Transfer'),
        ('cash', 'Bursar Cash Counter'),
        ('online', 'Credit Card / Web Portal'),
        ('scholarship', 'Institutional Scholarship / Waiver')
    ], string='Payment Method', tracking=True)

    payment_reference = fields.Char(
        string='Payment Reference / Slip #',
        help='Bank transaction reference or receipt voucher number.',
        tracking=True
    )
    payment_date = fields.Date(
        string='Latest Payment Date',
        tracking=True
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

    _challan_unique = models.Constraint(
        'UNIQUE(challan_number)',
        'A fee voucher with this Challan Number already exists!'
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('challan_number') or vals['challan_number'] == _('New'):
                vals['challan_number'] = self.env['ir.sequence'].next_by_code('unisphere.fee.challan') or _('New')
        records = super().create(vals_list)
        for record in records:
            if record.state not in ('draft', 'cancelled'):
                record._update_state()
        return records

    def write(self, vals):
        res = super().write(vals)
        # Avoid recursion: only check state if amounts or dates change and state wasn't explicitly written
        if any(f in vals for f in ('amount_due', 'amount_paid', 'due_date')) and 'state' not in vals:
            for record in self:
                if record.state not in ('draft', 'cancelled'):
                    record._update_state()
        return res

    @api.depends('student_id.name', 'challan_number', 'fee_type')
    def _compute_display_name(self):
        type_labels = dict(self._fields['fee_type'].selection)
        for record in self:
            s_name = record.student_id.name if record.student_id else ''
            c_num = record.challan_number or _('New')
            f_type = type_labels.get(record.fee_type, '')
            record.display_name = f"[{c_num}] {s_name} - {f_type}"

    @api.depends('amount_due', 'amount_paid')
    def _compute_balance_due(self):
        for record in self:
            record.balance_due = max(0.0, record.amount_due - record.amount_paid)

    def _update_state(self):
        today = fields.Date.today()
        for record in self:
            if record.state in ('draft', 'cancelled'):
                continue
            new_state = record.state
            if record.amount_paid >= record.amount_due and record.amount_due > 0:
                new_state = 'paid'
            elif record.due_date and record.due_date < today and record.balance_due > 0:
                new_state = 'overdue'
            elif record.amount_paid > 0:
                new_state = 'partial'
            else:
                new_state = 'posted'

            if new_state != record.state:
                super(UnisphereFee, record).write({'state': new_state})

    @api.constrains('amount_due', 'amount_paid')
    def _check_amounts(self):
        for record in self:
            if record.amount_due < 0:
                raise ValidationError(_("Amount due cannot be negative."))
            if record.amount_paid < 0:
                raise ValidationError(_("Amount paid cannot be negative."))
            if record.amount_paid > record.amount_due:
                raise ValidationError(_(
                    "Amount paid ($%(paid).2f) cannot exceed total amount due ($%(due).2f)!"
                ) % {
                    'paid': record.amount_paid,
                    'due': record.amount_due,
                })

    @api.constrains('issue_date', 'due_date')
    def _check_dates(self):
        for record in self:
            if record.issue_date and record.due_date and record.due_date < record.issue_date:
                raise ValidationError(_("Fee due date cannot be earlier than issue date."))

    def action_post_challan(self):
        for record in self:
            if record.state == 'draft':
                record.state = 'posted'
                record._update_state()

    def action_cancel(self):
        self.ensure_one()
        self.state = 'cancelled'

    def action_reset_draft(self):
        self.ensure_one()
        self.state = 'draft'

    def action_register_payment(self):
        self.ensure_one()
        return {
            'name': _('Register Fee Payment - %s') % self.challan_number,
            'type': 'ir.actions.act_window',
            'res_model': 'unisphere.fee.payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_fee_id': self.id,
                'default_payment_amount': self.balance_due,
            },
        }
