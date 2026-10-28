# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError
from odoo.tools import mute_logger


class TestAttendance(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Student = cls.env['unisphere.student']
        cls.Department = cls.env['unisphere.department']
        cls.Partner = cls.env['res.partner']
        cls.Term = cls.env['unisphere.academic.term']
        cls.Course = cls.env['unisphere.course']
        cls.Section = cls.env['unisphere.course.section']
        cls.Enrollment = cls.env['unisphere.enrollment']
        cls.Attendance = cls.env['unisphere.attendance']
        cls.AttendanceWizard = cls.env['unisphere.attendance.wizard']

        cls.dept = cls.Department.create({
            'name': 'Test Attendance Dept',
            'code': 'TAD',
        })

        cls.term = cls.Term.create({
            'name': 'Test Term 2026',
            'code': 'TT26A',
            'start_date': '2026-01-01',
            'end_date': '2026-05-31',
        })

        cls.course = cls.Course.create({
            'name': 'Computer Networks',
            'code': 'CN201',
            'department_id': cls.dept.id,
            'credit_hours': 3,
        })

        cls.section = cls.Section.create({
            'course_id': cls.course.id,
            'term_id': cls.term.id,
            'section_code': 'SEC-A',
            'capacity': 30,
        })

        cls.partner_1 = cls.Partner.create({'name': 'Att Student One'})
        cls.student_1 = cls.Student.create({
            'partner_id': cls.partner_1.id,
            'student_id': 'TEST-ATT-0001',
            'department_id': cls.dept.id,
            'program': 'bs_cs',
        })

        cls.partner_2 = cls.Partner.create({'name': 'Att Student Two'})
        cls.student_2 = cls.Student.create({
            'partner_id': cls.partner_2.id,
            'student_id': 'TEST-ATT-0002',
            'department_id': cls.dept.id,
            'program': 'bs_cs',
        })

        cls.partner_3 = cls.Partner.create({'name': 'Att Student Unenrolled'})
        cls.student_3 = cls.Student.create({
            'partner_id': cls.partner_3.id,
            'student_id': 'TEST-ATT-0003',
            'department_id': cls.dept.id,
            'program': 'bs_cs',
        })

        # Enroll student 1 and 2
        cls.enr_1 = cls.Enrollment.create({
            'student_id': cls.student_1.id,
            'section_id': cls.section.id,
            'state': 'enrolled',
        })
        cls.enr_2 = cls.Enrollment.create({
            'student_id': cls.student_2.id,
            'section_id': cls.section.id,
            'state': 'enrolled',
        })

    def test_01_create_attendance_and_enrollment_link(self):
        """Test creating an attendance entry links to enrollment and updates metrics"""
        att = self.Attendance.create({
            'student_id': self.student_1.id,
            'section_id': self.section.id,
            'class_date': '2026-02-01',
            'state': 'present',
        })
        self.assertEqual(att.enrollment_id.id, self.enr_1.id)
        self.assertEqual(self.enr_1.total_sessions, 1)
        self.assertEqual(self.enr_1.attended_sessions, 1)
        self.assertEqual(self.enr_1.absent_sessions, 0)
        self.assertEqual(self.enr_1.attendance_rate, 100.0)

    def test_02_duplicate_attendance_constraint(self):
        """Test SQL constraint preventing duplicate attendance on same date and section"""
        self.Attendance.create({
            'student_id': self.student_1.id,
            'section_id': self.section.id,
            'class_date': '2026-02-02',
            'state': 'present',
        })
        with mute_logger('odoo.sql_db'):
            with self.assertRaises(Exception):
                with self.cr.savepoint():
                    self.Attendance.create({
                        'student_id': self.student_1.id,
                        'section_id': self.section.id,
                        'class_date': '2026-02-02',
                        'state': 'absent',
                    })

    def test_03_future_date_rejected(self):
        """Test that recording attendance for future dates is rejected"""
        future_date = fields.Date.today() + timedelta(days=10)
        with self.assertRaises(ValidationError):
            self.Attendance.create({
                'student_id': self.student_1.id,
                'section_id': self.section.id,
                'class_date': future_date,
                'state': 'present',
            })

    def test_04_unenrolled_student_attendance_rejected(self):
        """Test that attendance cannot be recorded for student not actively enrolled"""
        with self.assertRaises(ValidationError):
            self.Attendance.create({
                'student_id': self.student_3.id,
                'section_id': self.section.id,
                'class_date': '2026-02-03',
                'state': 'present',
            })

    def test_05_attendance_rate_calculation(self):
        """Test computation of attendance rate across present, late, and absent sessions"""
        # Session 1: Present
        self.Attendance.create({
            'student_id': self.student_1.id,
            'section_id': self.section.id,
            'class_date': '2026-02-04',
            'state': 'present',
        })
        # Session 2: Late
        self.Attendance.create({
            'student_id': self.student_1.id,
            'section_id': self.section.id,
            'class_date': '2026-02-05',
            'state': 'late',
        })
        # Session 3: Absent
        self.Attendance.create({
            'student_id': self.student_1.id,
            'section_id': self.section.id,
            'class_date': '2026-02-06',
            'state': 'absent',
        })
        # Session 4: Present
        self.Attendance.create({
            'student_id': self.student_1.id,
            'section_id': self.section.id,
            'class_date': '2026-02-07',
            'state': 'present',
        })

        self.assertEqual(self.enr_1.total_sessions, 4)
        self.assertEqual(self.enr_1.attended_sessions, 3)  # 2 present + 1 late
        self.assertEqual(self.enr_1.absent_sessions, 1)
        self.assertEqual(self.enr_1.attendance_rate, 75.0)

    def test_06_attendance_wizard_execution(self):
        """Test batch recording via attendance wizard"""
        wizard = self.AttendanceWizard.with_context(default_section_id=self.section.id).create({
            'section_id': self.section.id,
            'class_date': '2026-02-08',
        })
        self.assertEqual(len(wizard.line_ids), 2)

        # Mark line 1 present, line 2 absent
        for line in wizard.line_ids:
            if line.student_id.id == self.student_1.id:
                line.state = 'present'
            elif line.student_id.id == self.student_2.id:
                line.state = 'absent'

        res = wizard.action_save_attendance()
        self.assertEqual(res['type'], 'ir.actions.client')

        # Check records created
        att_1 = self.Attendance.search([
            ('student_id', '=', self.student_1.id),
            ('section_id', '=', self.section.id),
            ('class_date', '=', '2026-02-08'),
        ])
        att_2 = self.Attendance.search([
            ('student_id', '=', self.student_2.id),
            ('section_id', '=', self.section.id),
            ('class_date', '=', '2026-02-08'),
        ])
        self.assertTrue(att_1)
        self.assertEqual(att_1.state, 'present')
        self.assertTrue(att_2)
        self.assertEqual(att_2.state, 'absent')
