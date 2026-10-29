# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError
from odoo.tools import mute_logger


class TestAssessmentsGrades(TransactionCase):

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
        cls.Assessment = cls.env['unisphere.assessment']
        cls.Grade = cls.env['unisphere.grade']
        cls.GradeWizard = cls.env['unisphere.grade.wizard']

        cls.dept = cls.Department.create({
            'name': 'Test Grade Dept',
            'code': 'TGD',
        })

        cls.term = cls.Term.create({
            'name': 'Test Term 2026',
            'code': 'TT26G',
            'start_date': '2026-01-01',
            'end_date': '2026-05-31',
        })

        cls.course = cls.Course.create({
            'name': 'Operating Systems',
            'code': 'OS201',
            'department_id': cls.dept.id,
            'credit_hours': 4,
        })

        cls.section = cls.Section.create({
            'course_id': cls.course.id,
            'term_id': cls.term.id,
            'section_code': 'SEC-G1',
            'capacity': 30,
        })

        cls.partner_1 = cls.Partner.create({'name': 'Grade Student Alpha'})
        cls.student_1 = cls.Student.create({
            'partner_id': cls.partner_1.id,
            'student_id': 'TEST-GRD-0001',
            'department_id': cls.dept.id,
            'program': 'bs_cs',
        })

        cls.partner_2 = cls.Partner.create({'name': 'Grade Student Beta'})
        cls.student_2 = cls.Student.create({
            'partner_id': cls.partner_2.id,
            'student_id': 'TEST-GRD-0002',
            'department_id': cls.dept.id,
            'program': 'bs_cs',
        })

        cls.partner_3 = cls.Partner.create({'name': 'Grade Student Unenrolled'})
        cls.student_3 = cls.Student.create({
            'partner_id': cls.partner_3.id,
            'student_id': 'TEST-GRD-0003',
            'department_id': cls.dept.id,
            'program': 'bs_cs',
        })

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

    def test_01_assessment_weightage_validation(self):
        """Test assessment weightage and max marks validation"""
        # Negative max marks rejected
        with self.assertRaises(ValidationError):
            self.Assessment.create({
                'name': 'Invalid Max Marks',
                'section_id': self.section.id,
                'max_marks': 0,
                'weightage': 10,
            })

        # Weightage > 100 rejected
        with self.assertRaises(ValidationError):
            self.Assessment.create({
                'name': 'Invalid Weightage',
                'section_id': self.section.id,
                'max_marks': 100,
                'weightage': 110,
            })

        # Total section weightage exceeding 100% rejected
        a1 = self.Assessment.create({
            'name': 'Exam Part 1',
            'section_id': self.section.id,
            'max_marks': 100,
            'weightage': 60,
        })
        with self.assertRaises(ValidationError):
            self.Assessment.create({
                'name': 'Exam Part 2',
                'section_id': self.section.id,
                'max_marks': 100,
                'weightage': 50,  # 60 + 50 = 110% > 100%
            })
        a1.unlink()

    def test_02_grade_creation_and_scale_mapping(self):
        """Test letter grade and grade point computation from marks obtained"""
        assessment = self.Assessment.create({
            'name': 'Midterm Test',
            'section_id': self.section.id,
            'max_marks': 100,
            'weightage': 30,
        })

        # Student 1 gets 88 -> 'A', 4.00
        g1 = self.Grade.create({
            'assessment_id': assessment.id,
            'student_id': self.student_1.id,
            'marks_obtained': 88.0,
        })
        self.assertEqual(g1.percentage, 88.0)
        self.assertEqual(g1.letter_grade, 'A')
        self.assertEqual(g1.grade_point, 4.00)

        # Student 2 gets 72 -> 'B', 3.00
        g2 = self.Grade.create({
            'assessment_id': assessment.id,
            'student_id': self.student_2.id,
            'marks_obtained': 72.0,
        })
        self.assertEqual(g2.percentage, 72.0)
        self.assertEqual(g2.letter_grade, 'B')
        self.assertEqual(g2.grade_point, 3.00)

    def test_03_duplicate_grade_prevention(self):
        """Test unique constraint on (assessment_id, student_id)"""
        assessment = self.Assessment.create({
            'name': 'Quiz Alpha',
            'section_id': self.section.id,
            'max_marks': 20,
            'weightage': 10,
        })
        self.Grade.create({
            'assessment_id': assessment.id,
            'student_id': self.student_1.id,
            'marks_obtained': 18.0,
        })
        with mute_logger('odoo.sql_db'):
            with self.assertRaises(Exception):
                with self.cr.savepoint():
                    self.Grade.create({
                        'assessment_id': assessment.id,
                        'student_id': self.student_1.id,
                        'marks_obtained': 15.0,
                    })

    def test_04_marks_exceeding_max_rejected(self):
        """Test validation error when marks exceed maximum marks"""
        assessment = self.Assessment.create({
            'name': 'Quiz Beta',
            'section_id': self.section.id,
            'max_marks': 25,
            'weightage': 10,
        })
        with self.assertRaises(ValidationError):
            self.Grade.create({
                'assessment_id': assessment.id,
                'student_id': self.student_1.id,
                'marks_obtained': 30.0,  # 30 > 25
            })

    def test_05_unenrolled_student_grade_rejected(self):
        """Test that grading an unenrolled student is rejected"""
        assessment = self.Assessment.create({
            'name': 'Quiz Gamma',
            'section_id': self.section.id,
            'max_marks': 50,
            'weightage': 10,
        })
        with self.assertRaises(ValidationError):
            self.Grade.create({
                'assessment_id': assessment.id,
                'student_id': self.student_3.id,  # not enrolled
                'marks_obtained': 45.0,
            })

    def test_06_composite_final_grade_and_gpa_calculation(self):
        """Test composite enrollment final grade and student GPA computation"""
        a_hw = self.Assessment.create({
            'name': 'Homeworks',
            'section_id': self.section.id,
            'max_marks': 50,
            'weightage': 20,  # 20%
        })
        a_mid = self.Assessment.create({
            'name': 'Midterm',
            'section_id': self.section.id,
            'max_marks': 100,
            'weightage': 30,  # 30%
        })
        a_fin = self.Assessment.create({
            'name': 'Final Exam',
            'section_id': self.section.id,
            'max_marks': 100,
            'weightage': 50,  # 50%
        })

        # Student 1 scores:
        # HW: 50/50 (100% * 20 = 20.0)
        # Midterm: 80/100 (80% * 30 = 24.0)
        # Final: 90/100 (90% * 50 = 45.0)
        # Total = 89.0% -> 'A' (4.00 GPA)
        self.Grade.create({
            'assessment_id': a_hw.id,
            'student_id': self.student_1.id,
            'marks_obtained': 50.0,
        })
        self.Grade.create({
            'assessment_id': a_mid.id,
            'student_id': self.student_1.id,
            'marks_obtained': 80.0,
        })
        self.Grade.create({
            'assessment_id': a_fin.id,
            'student_id': self.student_1.id,
            'marks_obtained': 90.0,
        })

        self.assertEqual(self.enr_1.final_grade, 89.0)
        self.assertEqual(self.enr_1.letter_grade, 'A')
        self.assertEqual(self.enr_1.grade_point, 4.00)
        self.assertTrue(self.enr_1.is_passed)
        self.assertEqual(self.student_1.gpa, 4.00)
        self.assertEqual(self.student_1.earned_credits, 4)

    def test_07_grade_wizard_execution(self):
        """Test batch grading wizard operation"""
        assessment = self.Assessment.create({
            'name': 'Lab Practical 1',
            'section_id': self.section.id,
            'max_marks': 50,
            'weightage': 15,
        })
        wizard = self.GradeWizard.with_context(default_assessment_id=assessment.id).create({
            'assessment_id': assessment.id,
        })
        self.assertEqual(len(wizard.line_ids), 2)

        for line in wizard.line_ids:
            if line.student_id.id == self.student_1.id:
                line.marks_obtained = 45.0
            elif line.student_id.id == self.student_2.id:
                line.marks_obtained = 38.0

        res = wizard.action_save_grades()
        self.assertEqual(res['type'], 'ir.actions.client')

        g1 = self.Grade.search([('assessment_id', '=', assessment.id), ('student_id', '=', self.student_1.id)])
        g2 = self.Grade.search([('assessment_id', '=', assessment.id), ('student_id', '=', self.student_2.id)])
        self.assertTrue(g1)
        self.assertEqual(g1.marks_obtained, 45.0)
        self.assertTrue(g2)
        self.assertEqual(g2.marks_obtained, 38.0)
        self.assertEqual(assessment.state, 'grading')
