# -*- coding: utf-8 -*-
from datetime import date, timedelta
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError
from odoo.tools import mute_logger


class TestFeeManagement(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Student = cls.env['unisphere.student']
        cls.Department = cls.env['unisphere.department']
        cls.Partner = cls.env['res.partner']
        cls.Term = cls.env['unisphere.academic.term']
        cls.Fee = cls.env['unisphere.fee']
        cls.FeeWizard = cls.env['unisphere.fee.payment.wizard']

        cls.dept = cls.Department.create({
            'name': 'Test Bursar Dept',
            'code': 'TBD',
        })

        cls.term = cls.Term.create({
            'name': 'Bursar Term 2026',
            'code': 'BT26',
            'start_date': date(2026, 1, 1),
            'end_date': date(2026, 5, 31),
        })

        cls.partner = cls.Partner.create({'name': 'Bursar Student Alpha'})
        cls.student = cls.Student.create({
            'partner_id': cls.partner.id,
            'student_id': 'TEST-BURSAR-0001',
            'department_id': cls.dept.id,
            'program': 'bs_cs',
        })

    def test_01_challan_sequence_generation(self):
        """Test automatic sequence generation for fee challans."""
        fee = self.Fee.create({
            'student_id': self.student.id,
            'term_id': self.term.id,
            'fee_type': 'tuition',
            'issue_date': date.today(),
            'due_date': date.today() + timedelta(days=30),
            'amount_due': 1200.0,
        })
        self.assertTrue(fee.challan_number)
        self.assertNotEqual(fee.challan_number, 'New')
        self.assertTrue(fee.challan_number.startswith('NUT-FEE-'))
        self.assertIn(self.student.name, fee.display_name)
        self.assertEqual(fee.balance_due, 1200.0)
        self.assertEqual(fee.state, 'draft')

    def test_02_balance_due_and_state_transitions(self):
        """Test balance due calculations and automatic workflow states."""
        fee = self.Fee.create({
            'student_id': self.student.id,
            'term_id': self.term.id,
            'fee_type': 'tuition',
            'issue_date': date.today(),
            'due_date': date.today() + timedelta(days=30),
            'amount_due': 1000.0,
            'amount_paid': 0.0,
        })
        # Issue challan to move to posted
        fee.action_post_challan()
        self.assertEqual(fee.state, 'posted')
        self.assertEqual(fee.balance_due, 1000.0)

        # Make partial payment
        fee.write({'amount_paid': 400.0})
        self.assertEqual(fee.balance_due, 600.0)
        self.assertEqual(fee.state, 'partial')

        # Make complete payment
        fee.write({'amount_paid': 1000.0})
        self.assertEqual(fee.balance_due, 0.0)
        self.assertEqual(fee.state, 'paid')

    def test_03_overdue_state_detection(self):
        """Test that past due date with outstanding balance sets state to overdue."""
        past_date = date.today() - timedelta(days=15)
        fee = self.Fee.create({
            'student_id': self.student.id,
            'term_id': self.term.id,
            'fee_type': 'tuition',
            'issue_date': past_date - timedelta(days=30),
            'due_date': past_date,
            'amount_due': 1500.0,
            'amount_paid': 500.0,
            'state': 'posted',
        })
        # Since due_date is in past and balance is outstanding, state becomes overdue
        self.assertEqual(fee.state, 'overdue')
        self.assertEqual(fee.balance_due, 1000.0)

    def test_04_negative_amounts_validation(self):
        """Test validation constraint against negative amounts."""
        with self.assertRaises(ValidationError):
            self.Fee.create({
                'student_id': self.student.id,
                'term_id': self.term.id,
                'fee_type': 'tuition',
                'issue_date': date.today(),
                'due_date': date.today() + timedelta(days=10),
                'amount_due': -500.0,
            })

        with self.assertRaises(ValidationError):
            self.Fee.create({
                'student_id': self.student.id,
                'term_id': self.term.id,
                'fee_type': 'tuition',
                'issue_date': date.today(),
                'due_date': date.today() + timedelta(days=10),
                'amount_due': 500.0,
                'amount_paid': -50.0,
            })

    def test_05_overpayment_validation(self):
        """Test validation constraint preventing payments exceeding amount due."""
        with self.assertRaises(ValidationError):
            self.Fee.create({
                'student_id': self.student.id,
                'term_id': self.term.id,
                'fee_type': 'tuition',
                'issue_date': date.today(),
                'due_date': date.today() + timedelta(days=10),
                'amount_due': 1000.0,
                'amount_paid': 1200.0,
            })

    def test_06_due_date_prior_to_issue_date_validation(self):
        """Test validation constraint that due date cannot precede issue date."""
        today = date.today()
        with self.assertRaises(ValidationError):
            self.Fee.create({
                'student_id': self.student.id,
                'term_id': self.term.id,
                'fee_type': 'tuition',
                'issue_date': today,
                'due_date': today - timedelta(days=5),
                'amount_due': 1000.0,
            })

    def test_07_payment_wizard_flow(self):
        """Test registering payment via the unisphere.fee.payment.wizard."""
        fee = self.Fee.create({
            'student_id': self.student.id,
            'term_id': self.term.id,
            'fee_type': 'tuition',
            'issue_date': date.today(),
            'due_date': date.today() + timedelta(days=30),
            'amount_due': 2000.0,
            'state': 'posted',
        })

        # Launch wizard with fee in context
        wizard_vals = self.FeeWizard.with_context(default_fee_id=fee.id).default_get([
            'fee_id', 'payment_amount'
        ])
        self.assertEqual(wizard_vals['fee_id'], fee.id)
        self.assertEqual(wizard_vals['payment_amount'], 2000.0)

        # Confirm partial payment of 800
        wizard = self.FeeWizard.create({
            'fee_id': fee.id,
            'payment_amount': 800.0,
            'payment_method': 'bank_transfer',
            'payment_reference': 'TEST-TRX-001',
            'payment_date': date.today(),
        })
        wizard.action_confirm_payment()

        self.assertEqual(fee.amount_paid, 800.0)
        self.assertEqual(fee.balance_due, 1200.0)
        self.assertEqual(fee.payment_method, 'bank_transfer')
        self.assertEqual(fee.payment_reference, 'TEST-TRX-001')
        self.assertEqual(fee.state, 'partial')

    def test_08_payment_wizard_excess_rejection(self):
        """Test that payment wizard rejects payments greater than remaining balance."""
        fee = self.Fee.create({
            'student_id': self.student.id,
            'term_id': self.term.id,
            'fee_type': 'tuition',
            'issue_date': date.today(),
            'due_date': date.today() + timedelta(days=30),
            'amount_due': 500.0,
            'state': 'posted',
        })

        wizard = self.FeeWizard.create({
            'fee_id': fee.id,
            'payment_amount': 600.0,
            'payment_method': 'cash',
            'payment_reference': 'RCP-999',
        })
        with self.assertRaises(ValidationError):
            wizard.action_confirm_payment()

    def test_09_student_fee_metrics_and_status(self):
        """Test computed financial rollups on student profile."""
        partner_b = self.Partner.create({'name': 'Bursar Student Beta'})
        student_b = self.Student.create({
            'partner_id': partner_b.id,
            'student_id': 'TEST-BURSAR-0002',
            'department_id': self.dept.id,
            'program': 'bs_se',
        })

        # No fees initially
        student_b._compute_fee_metrics()
        self.assertEqual(student_b.total_invoiced, 0.0)
        self.assertEqual(student_b.total_paid, 0.0)
        self.assertEqual(student_b.balance_due, 0.0)
        self.assertEqual(student_b.fee_status, 'clear')

        # Add tuition fee ($1500, paid $500)
        fee_1 = self.Fee.create({
            'student_id': student_b.id,
            'term_id': self.term.id,
            'fee_type': 'tuition',
            'issue_date': date.today(),
            'due_date': date.today() + timedelta(days=30),
            'amount_due': 1500.0,
            'amount_paid': 500.0,
            'state': 'posted',
        })

        # Add lab fee ($200, paid $200)
        fee_2 = self.Fee.create({
            'student_id': student_b.id,
            'term_id': self.term.id,
            'fee_type': 'lab',
            'issue_date': date.today(),
            'due_date': date.today() + timedelta(days=30),
            'amount_due': 200.0,
            'amount_paid': 200.0,
            'state': 'posted',
        })

        student_b._compute_fee_metrics()
        self.assertEqual(student_b.total_invoiced, 1700.0)
        self.assertEqual(student_b.total_paid, 700.0)
        self.assertEqual(student_b.balance_due, 1000.0)
        self.assertEqual(student_b.fee_status, 'dues_pending')

        # Test action_view_fees returns correct action domain
        action = student_b.action_view_fees()
        self.assertEqual(action['res_model'], 'unisphere.fee')
        self.assertEqual(action['domain'], [('student_id', '=', student_b.id)])
