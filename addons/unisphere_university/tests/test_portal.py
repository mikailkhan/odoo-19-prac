# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from werkzeug.exceptions import Forbidden


class TestStudentPortal(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Student = cls.env['unisphere.student']
        cls.Enrollment = cls.env['unisphere.enrollment']
        cls.Attendance = cls.env['unisphere.attendance']
        cls.Assessment = cls.env['unisphere.assessment']
        cls.Grade = cls.env['unisphere.grade']
        cls.Fee = cls.env['unisphere.fee']

        # Demo Students and Users
        cls.student_ayesha = cls.env.ref('unisphere_university.student_ayesha')
        cls.user_ayesha = cls.env.ref('unisphere_university.user_student_ayesha')

        cls.student_usman = cls.env.ref('unisphere_university.student_usman')
        cls.user_usman = cls.env.ref('unisphere_university.user_student_usman')

        cls.section_cs = cls.env.ref('unisphere_university.section_cs101_1a')
        cls.section_ai = cls.env.ref('unisphere_university.section_ai201_1a')

    def test_01_student_portal_row_level_isolation(self):
        """Test that record rules strictly isolate students to their own records."""
        ayesha_env = self.env['unisphere.student'].with_user(self.user_ayesha)
        usman_env = self.env['unisphere.student'].with_user(self.user_usman)

        # 1. Student profile visibility
        ayesha_students = ayesha_env.search([])
        self.assertEqual(len(ayesha_students), 1)
        self.assertEqual(ayesha_students.id, self.student_ayesha.id)

        usman_students = usman_env.search([])
        self.assertEqual(len(usman_students), 1)
        self.assertEqual(usman_students.id, self.student_usman.id)

        # 2. Fee challan isolation
        ayesha_fees = self.env['unisphere.fee'].with_user(self.user_ayesha).search([])
        self.assertTrue(all(f.student_id == self.student_ayesha for f in ayesha_fees))
        self.assertNotIn('NUT-2024-FEE-0003', ayesha_fees.mapped('challan_number'))

        usman_fees = self.env['unisphere.fee'].with_user(self.user_usman).search([])
        self.assertTrue(all(f.student_id == self.student_usman for f in usman_fees))
        self.assertIn('NUT-2024-FEE-0003', usman_fees.mapped('challan_number'))

    def test_02_grade_publication_security_rule(self):
        """Test that students can only see grades when the assessment is published."""
        test_section = self.env['unisphere.course.section'].create({
            'course_id': self.section_cs.course_id.id,
            'term_id': self.section_cs.term_id.id,
            'section_code': 'TEST-PUB',
            'instructor_id': self.section_cs.instructor_id.id,
            'capacity': 30,
        })
        self.Enrollment.create({
            'student_id': self.student_ayesha.id,
            'section_id': test_section.id,
            'state': 'enrolled',
        })

        draft_assessment = self.Assessment.create({
            'name': 'Pop Quiz 99 (Unpublished)',
            'section_id': test_section.id,
            'assessment_type': 'quiz',
            'max_marks': 20.0,
            'weightage': 15.0,
            'state': 'draft',
        })

        grade = self.Grade.create({
            'assessment_id': draft_assessment.id,
            'student_id': self.student_ayesha.id,
            'marks_obtained': 19.0,
        })

        # Under Ayesha's user session, the draft grade MUST NOT be visible
        ayesha_grades = self.env['unisphere.grade'].with_user(self.user_ayesha).search([('id', '=', grade.id)])
        self.assertFalse(ayesha_grades, "Draft assessment grades must be hidden from students via ir.rule!")

        # Publish the assessment
        draft_assessment.write({'state': 'published'})

        # Now the published grade MUST be visible to Ayesha
        ayesha_grades_after = self.env['unisphere.grade'].with_user(self.user_ayesha).search([('id', '=', grade.id)])
        self.assertTrue(ayesha_grades_after, "Published assessment grades must be visible to enrolled student!")

        # But Usman must NOT see Ayesha's published grade
        usman_grades = self.env['unisphere.grade'].with_user(self.user_usman).search([('id', '=', grade.id)])
        self.assertFalse(usman_grades, "A student must never see another student's published grade!")

    def test_03_course_enrollment_boundary(self):
        """Test that enrolled sections are accessible while un-enrolled sections are protected."""
        # Ayesha is enrolled in section_cs101_1a
        ayesha_enrollments = self.Enrollment.search([
            ('student_id', '=', self.student_ayesha.id),
            ('section_id', '=', self.section_cs.id)
        ])
        self.assertTrue(bool(ayesha_enrollments))

        # Ayesha is NOT enrolled in section_ai201_1a
        ayesha_ai_enrollments = self.Enrollment.search([
            ('student_id', '=', self.student_ayesha.id),
            ('section_id', '=', self.section_ai.id)
        ])
        self.assertFalse(bool(ayesha_ai_enrollments))
