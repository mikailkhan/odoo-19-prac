# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from odoo.tools import mute_logger


class TestAcademicFoundation(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Department = cls.env['unisphere.department']
        cls.Term = cls.env['unisphere.academic.term']
        cls.Course = cls.env['unisphere.course']
        cls.Section = cls.env['unisphere.course.section']

        cls.dept_math = cls.Department.create({
            'name': 'Department of Mathematics',
            'code': 'MATH',
        })

        cls.term_test = cls.Term.create({
            'name': 'Test Term 2025',
            'code': 'TT25',
            'start_date': '2025-01-01',
            'end_date': '2025-05-31',
        })

        cls.course_calc = cls.Course.create({
            'name': 'Calculus I',
            'code': 'MATH101',
            'department_id': cls.dept_math.id,
            'credit_hours': 3,
        })

    def test_01_department_unique_code(self):
        """Test that duplicate department codes are rejected"""
        with mute_logger('odoo.sql_db'):
            with self.assertRaises(Exception):
                with self.cr.savepoint():
                    self.Department.create({
                        'name': 'Another Math Dept',
                        'code': 'MATH',
                    })

    def test_02_term_date_validation(self):
        """Test that start_date must precede end_date"""
        with self.assertRaises(ValidationError):
            self.Term.create({
                'name': 'Invalid Dates Term',
                'code': 'INV1',
                'start_date': '2025-06-01',
                'end_date': '2025-01-01',
            })

    def test_03_course_credit_hours(self):
        """Test that credit hours must be between 1 and 6"""
        with self.assertRaises(ValidationError):
            self.Course.create({
                'name': 'Overloaded Course',
                'code': 'OVER101',
                'department_id': self.dept_math.id,
                'credit_hours': 10,
            })

    def test_04_section_capacity_validation(self):
        """Test that section capacity must be > 0"""
        with self.assertRaises(ValidationError):
            self.Section.create({
                'course_id': self.course_calc.id,
                'term_id': self.term_test.id,
                'section_code': 'SEC-0',
                'capacity': 0,
            })

    def test_05_section_seats_available_compute(self):
        """Test that seats_available is correctly computed from capacity"""
        section = self.Section.create({
            'course_id': self.course_calc.id,
            'term_id': self.term_test.id,
            'section_code': 'SEC-1',
            'capacity': 30,
        })
        self.assertEqual(section.seats_available, 30)
        self.assertEqual(section.name, "MATH101 - SEC-1 (TT25)")
