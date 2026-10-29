# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class UnisphereFeePaymentWizard(models.TransientModel):
    _name = 'unisphere.fee.payment.wizard'
    _description = 'Fee Payment Registration Wizard'

    fee_id = fields.Many2one(
        'unisphere.fee',
        string='Fee Challan',
        required=True
    )
    student_id = fields.Many2one(
        related='fee_id.student_id',
        string='Student',
        readonly=True
    )
    challan_number = fields.Char(
        related='fee_id.challan_number',
        string='Challan Number',
        readonly=True
    )
    amount_due = fields.Float(
        related='fee_id.amount_due',
        string='Total Invoiced ($)',
        readonly=True
    )
    amount_paid = fields.Float(
        related='fee_id.amount_paid',
        string='Already Paid ($)',
        readonly=True
    )
    balance_due = fields.Float(
        related='fee_id.balance_due',
        string='Outstanding Balance ($)',
        readonly=True
    )
    payment_amount = fields.Float(
        string='Payment Amount ($)',
        required=True,
        digits=(10, 2)
    )
    payment_method = fields.Selection([
        ('bank_transfer', 'Bank Deposit / 1Link Transfer'),
        ('cash', 'Bursar Cash Counter'),
        ('online', 'Credit Card / Web Portal'),
        ('scholarship', 'Institutional Scholarship / Waiver')
    ], string='Payment Method', required=True, default='bank_transfer')

    payment_reference = fields.Char(
        string='Payment Reference / Slip #',
        required=True,
        help='Bank transaction reference or receipt voucher number.'
    )
    payment_date = fields.Date(
        string='Payment Date',
        required=True,
        default=fields.Date.today
    )
    notes = fields.Char(
        string='Internal Notes',
        help='Optional observations or receipt notes.'
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        fee_id = self.env.context.get('default_fee_id') or self.env.context.get('active_id')
        if fee_id:
            fee = self.env['unisphere.fee'].browse(fee_id)
            if fee.exists():
                res['fee_id'] = fee.id
                res['payment_amount'] = fee.balance_due
        return res

    def action_confirm_payment(self):
        self.ensure_one()
        if self.payment_amount <= 0:
            raise ValidationError(_("Payment amount must be greater than zero."))
        if self.payment_amount > self.balance_due:
            raise ValidationError(_(
                "Payment amount ($%(pay).2f) cannot exceed outstanding balance ($%(bal).2f)!"
            ) % {
                'pay': self.payment_amount,
                'bal': self.balance_due,
            })

        fee = self.fee_id
        new_paid = fee.amount_paid + self.payment_amount
        fee.write({
            'amount_paid': new_paid,
            'payment_method': self.payment_method,
            'payment_reference': self.payment_reference,
            'payment_date': self.payment_date,
        })

        # Post receipt notification in chatter
        method_label = dict(self._fields['payment_method'].selection).get(self.payment_method, self.payment_method)
        fee.message_post(body=_(
            "<strong>Payment Received:</strong> $%(amount).2f via %(method)s.<br/>"
            "Reference: %(ref)s | Date: %(date)s<br/>"
            "Remaining Balance: $%(bal).2f"
        ) % {
            'amount': self.payment_amount,
            'method': method_label,
            'ref': self.payment_reference,
            'date': self.payment_date,
            'bal': fee.balance_due,
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Payment Recorded'),
                'message': _('Successfully recorded $%(amount).2f payment for %(challan)s.') % {
                    'amount': self.payment_amount,
                    'challan': fee.challan_number,
                },
                'type': 'success',
                'sticky': False,
            }
        }
