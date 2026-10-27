# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from odoo.tools import mute_logger


class TestStudentsFaculty(TransactionCase):

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

        cls.dept_cs = cls.Department.create({
            'name': 'Test CS Department',
            'code': 'TCS',
        })

        cls.term_test = cls.Term.create({
            'name': 'Test Term Fall',
            'code': 'TTF',
            'start_date': '2025-09-01',
            'end_date': '2026-01-31',
        })

        cls.course_prog = cls.Course.create({
            'name': 'Programming Fundamentals',
            'code': 'PF101',
            'department_id': cls.dept_cs.id,
            'credit_hours': 3,
        })

        cls.partner_prof = cls.Partner.create({
            'name': 'Prof. Alan Turing',
            'email': 'a.turing@northstar.edu',
            'phone': '+92 51 0000 1111',
        })

        cls.faculty_alan = cls.Faculty.create({
            'partner_id': cls.partner_prof.id,
            'faculty_id': 'TEST-FAC-0001',
            'department_id': cls.dept_cs.id,
            'designation': 'professor',
        })

        cls.partner_stud = cls.Partner.create({
            'name': 'Ada Lovelace',
            'email': 'ada@student.northstar.edu',
            'phone': '+92 300 0000 2222',
        })

        cls.student_ada = cls.Student.create({
            'partner_id': cls.partner_stud.id,
            'student_id': 'TEST-2025-CS-0001',
            'department_id': cls.dept_cs.id,
            'program': 'bs_cs',
            'admission_date': '2025-09-01',
        })

    def test_01_student_unique_id(self):
        """Test that duplicate student ID raises exception"""
        partner_duplicate = self.Partner.create({'name': 'Duplicate Student'})
        with mute_logger('odoo.sql_db'):
            with self.assertRaises(Exception):
                with self.cr.savepoint():
                    self.Student.create({
                        'partner_id': partner_duplicate.id,
                        'student_id': 'TEST-2025-CS-0001',
                        'department_id': self.dept_cs.id,
                        'program': 'bs_cs',
                    })

    def test_02_faculty_unique_id(self):
        """Test that duplicate faculty ID raises exception"""
        partner_duplicate = self.Partner.create({'name': 'Duplicate Faculty'})
        with mute_logger('odoo.sql_db'):
            with self.assertRaises(Exception):
                with self.cr.savepoint():
                    self.Faculty.create({
                        'partner_id': partner_duplicate.id,
                        'faculty_id': 'TEST-FAC-0001',
                        'department_id': self.dept_cs.id,
                    })

    def test_03_student_contact_linkage(self):
        """Test that student details synchronize with res.partner"""
        self.assertEqual(self.student_ada.name, 'Ada Lovelace')
        self.assertEqual(self.student_ada.email, 'ada@student.northstar.edu')
        self.assertEqual(self.student_ada.phone, '+92 300 0000 2222')
        self.assertEqual(self.student_ada.display_name, '[TEST-2025-CS-0001] Ada Lovelace')

    def test_04_faculty_sections_smart_button(self):
        """Test that assigned sections correctly update faculty section_count"""
        self.assertEqual(self.faculty_alan.section_count, 0)
        self.Section.create({
            'course_id': self.course_prog.id,
            'term_id': self.term_test.id,
            'section_code': 'SEC-T1',
            'instructor_id': self.faculty_alan.id,
            'capacity': 40,
        })
        self.assertEqual(self.faculty_alan.section_count, 1)
