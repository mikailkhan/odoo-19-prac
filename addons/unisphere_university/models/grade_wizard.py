# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class UnisphereGradeWizard(models.TransientModel):
    _name = 'unisphere.grade.wizard'
    _description = 'Batch Grade Entry Wizard'

    assessment_id = fields.Many2one(
        'unisphere.assessment',
        string='Assessment Component',
        required=True
    )
    section_id = fields.Many2one(
        related='assessment_id.section_id',
        string='Course Section',
        readonly=True
    )
    max_marks = fields.Float(
        related='assessment_id.max_marks',
        string='Maximum Marks',
        readonly=True
    )
    line_ids = fields.One2many(
        'unisphere.grade.wizard.line',
        'wizard_id',
        string='Grade Roster Lines'
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        assessment_id = self.env.context.get('default_assessment_id') or self.env.context.get('active_id')
        if assessment_id:
            res['assessment_id'] = assessment_id
            assessment = self.env['unisphere.assessment'].browse(assessment_id)
            if assessment.exists() and assessment.section_id:
                enrollments = self.env['unisphere.enrollment'].search([
                    ('section_id', '=', assessment.section_id.id),
                    ('state', '=', 'enrolled'),
                ])
                lines = []
                for enr in enrollments:
                    existing_grade = self.env['unisphere.grade'].search([
                        ('assessment_id', '=', assessment.id),
                        ('student_id', '=', enr.student_id.id),
                    ], limit=1)
                    lines.append((0, 0, {
                        'student_id': enr.student_id.id,
                        'marks_obtained': existing_grade.marks_obtained if existing_grade else 0.0,
                        'remarks': existing_grade.remarks if existing_grade else '',
                    }))
                res['line_ids'] = lines
        return res

    def action_save_grades(self):
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_("No students found in the roster for this assessment's section!"))

        Grade = self.env['unisphere.grade']
        for line in self.line_ids:
            if line.marks_obtained < 0 or line.marks_obtained > self.max_marks:
                raise ValidationError(_(
                    "Marks obtained for %(student)s (%(obtained)s) must be between 0 and %(max)s!"
                ) % {
                    'student': line.student_id.name,
                    'obtained': line.marks_obtained,
                    'max': self.max_marks,
                })

            existing = Grade.search([
                ('assessment_id', '=', self.assessment_id.id),
                ('student_id', '=', line.student_id.id),
            ], limit=1)

            if existing:
                existing.write({
                    'marks_obtained': line.marks_obtained,
                    'remarks': line.remarks or existing.remarks,
                    'state': 'graded',
                })
            else:
                Grade.create({
                    'assessment_id': self.assessment_id.id,
                    'student_id': line.student_id.id,
                    'marks_obtained': line.marks_obtained,
                    'remarks': line.remarks or '',
                    'state': 'graded',
                })

        # Update assessment state to 'grading' if it was in 'draft' or 'announced'
        if self.assessment_id.state in ('draft', 'announced'):
            self.assessment_id.state = 'grading'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Grades Recorded'),
                'message': _('Successfully recorded marks for %d students.') % len(self.line_ids),
                'type': 'success',
                'sticky': False,
            }
        }


class UnisphereGradeWizardLine(models.TransientModel):
    _name = 'unisphere.grade.wizard.line'
    _description = 'Grade Entry Line'

    wizard_id = fields.Many2one('unisphere.grade.wizard', required=True, ondelete='cascade')
    student_id = fields.Many2one('unisphere.student', string='Student', required=True, readonly=True)
    student_reg_no = fields.Char(related='student_id.student_id', string='Registration No', readonly=True)
    marks_obtained = fields.Float(string='Marks Obtained', required=True, default=0.0)
    remarks = fields.Char(string='Remarks')
