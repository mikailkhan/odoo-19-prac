# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from odoo.tools import mute_logger


class TestEnrollment(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Student = cls.env['unisphere.student']
        cls.Faculty = cls.env['unisphere.faculty']
        cls.Department = cls.env['unisphere.department']
        cls.Partner = cls.env['res.partner']
        cls.Term = cls.env['unisphere.academic.term']
        cls.Course = cls.env['unisphere.course']
        cls.Section = cls.env['unisphere.course.section']
        cls.Enrollment = cls.env['unisphere.enrollment']

        cls.dept = cls.Department.create({
            'name': 'Test Enrollment Dept',
            'code': 'TED',
        })

        cls.term = cls.Term.create({
            'name': 'Test Term 2026',
            'code': 'TT26',
            'start_date': '2026-01-01',
            'end_date': '2026-05-31',
        })

        cls.course = cls.Course.create({
            'name': 'Database Systems',
            'code': 'DBS101',
            'department_id': cls.dept.id,
            'credit_hours': 3,
        })

        cls.section_small = cls.Section.create({
            'course_id': cls.course.id,
            'term_id': cls.term.id,
            'section_code': 'SEC-CAP1',
            'capacity': 1,
        })

        cls.partner_1 = cls.Partner.create({'name': 'Student Alice'})
        cls.student_1 = cls.Student.create({
            'partner_id': cls.partner_1.id,
            'student_id': 'TEST-ENR-0001',
            'department_id': cls.dept.id,
            'program': 'bs_cs',
        })

        cls.partner_2 = cls.Partner.create({'name': 'Student Bob'})
        cls.student_2 = cls.Student.create({
            'partner_id': cls.partner_2.id,
            'student_id': 'TEST-ENR-0002',
            'department_id': cls.dept.id,
            'program': 'bs_cs',
        })

    def test_01_duplicate_enrollment_prevention(self):
        """Test that a student cannot be enrolled in the same section twice"""
        self.Enrollment.create({
            'student_id': self.student_1.id,
            'section_id': self.section_small.id,
        })
        with mute_logger('odoo.sql_db'):
            with self.assertRaises(Exception):
                with self.cr.savepoint():
                    self.Enrollment.create({
                        'student_id': self.student_1.id,
                        'section_id': self.section_small.id,
                    })

    def test_02_section_capacity_limit(self):
        """Test that section capacity limits are strictly enforced"""
        # Enroll first student (takes 1 available seat)
        self.Enrollment.create({
            'student_id': self.student_1.id,
            'section_id': self.section_small.id,
            'state': 'enrolled',
        })
        self.assertEqual(self.section_small.enrolled_count, 1)
        self.assertEqual(self.section_small.seats_available, 0)

        # Attempting to enroll 2nd student into a section with capacity=1 must raise ValidationError
        with self.assertRaises(ValidationError):
            self.Enrollment.create({
                'student_id': self.student_2.id,
                'section_id': self.section_small.id,
                'state': 'enrolled',
            })

    def test_03_dropped_enrollment_frees_seat(self):
        """Test that dropping an enrollment frees a seat and decrements enrolled_count"""
        enr = self.Enrollment.create({
            'student_id': self.student_1.id,
            'section_id': self.section_small.id,
            'state': 'enrolled',
        })
        self.assertEqual(self.section_small.enrolled_count, 1)
        self.assertEqual(self.section_small.seats_available, 0)

        # Drop enrollment
        enr.action_drop_enrollment()
        self.assertEqual(enr.state, 'dropped')
        self.assertEqual(self.section_small.enrolled_count, 0)
        self.assertEqual(self.section_small.seats_available, 1)
