# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class TestExecutiveDashboard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Dashboard = cls.env['unisphere.dashboard']
        cls.Term = cls.env['unisphere.academic.term']
        cls.Student = cls.env['unisphere.student']
        cls.Department = cls.env['unisphere.department']
        cls.Fee = cls.env['unisphere.fee']

    def test_01_get_dashboard_data_structure(self):
        """Test that get_dashboard_data returns complete payload structure."""
        data = self.Dashboard.get_dashboard_data()
        self.assertIn('terms', data)
        self.assertIn('active_term_id', data)
        self.assertIn('kpis', data)
        self.assertIn('fee_velocity', data)
        self.assertIn('departments', data)
        self.assertIn('recent_students', data)
        self.assertIn('alerts', data)

        kpis = data['kpis']
        self.assertIn('total_students', kpis)
        self.assertIn('active_enrollments', kpis)
        self.assertIn('faculty_count', kpis)
        self.assertIn('active_sections', kpis)
        self.assertIn('avg_gpa', kpis)
        self.assertIn('avg_attendance', kpis)
        self.assertIn('total_invoiced', kpis)
        self.assertIn('total_collected', kpis)
        self.assertIn('total_receivable', kpis)
        self.assertIn('collection_rate', kpis)

        # Basic type and boundary checks
        self.assertIsInstance(kpis['total_students'], int)
        self.assertIsInstance(kpis['collection_rate'], float)
        self.assertGreaterEqual(kpis['collection_rate'], 0.0)
        self.assertLessEqual(kpis['collection_rate'], 100.0)

    def test_02_department_breakdown_and_fee_velocity(self):
        """Test department metrics and multi-segment fee velocity calculations."""
        data = self.Dashboard.get_dashboard_data()
        departments = data['departments']
        self.assertTrue(len(departments) > 0)
        for dept in departments:
            self.assertIn('id', dept)
            self.assertIn('name', dept)
            self.assertIn('code', dept)
            self.assertIn('student_count', dept)
            self.assertIn('section_count', dept)
            self.assertIn('color', dept)

        fee_velocity = data['fee_velocity']
        self.assertIn('collected', fee_velocity)
        self.assertIn('pending', fee_velocity)
        self.assertIn('overdue', fee_velocity)
        self.assertIn('collected_pct', fee_velocity)
        self.assertIn('pending_pct', fee_velocity)
        self.assertIn('overdue_pct', fee_velocity)

    def test_03_term_filtering(self):
        """Test filtering dashboard metrics by specific academic term."""
        active_term = self.Term.search([('state', '=', 'active')], limit=1)
        if active_term:
            data = self.Dashboard.get_dashboard_data(term_id=active_term.id)
            self.assertEqual(data['active_term_id'], active_term.id)
            self.assertEqual(data['active_term_name'], active_term.name)
