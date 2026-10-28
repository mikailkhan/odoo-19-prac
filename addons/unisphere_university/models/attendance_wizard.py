# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class UnisphereAttendanceWizard(models.TransientModel):
    _name = 'unisphere.attendance.wizard'
    _description = 'Quick Attendance Register Entry Wizard'

    section_id = fields.Many2one(
        'unisphere.course.section',
        string='Course Section',
        required=True,
    )
    class_date = fields.Date(
        string='Session Date',
        required=True,
        default=fields.Date.today,
    )
    line_ids = fields.One2many(
        'unisphere.attendance.wizard.line',
        'wizard_id',
        string='Student Roster Lines'
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        section_id = self.env.context.get('default_section_id') or self.env.context.get('active_id')
        if section_id:
            res['section_id'] = section_id
            enrollments = self.env['unisphere.enrollment'].search([
                ('section_id', '=', section_id),
                ('state', '=', 'enrolled'),
            ])
            lines = []
            for enr in enrollments:
                lines.append((0, 0, {
                    'student_id': enr.student_id.id,
                    'state': 'present',
                    'remarks': '',
                }))
            res['line_ids'] = lines
        return res

    @api.onchange('section_id')
    def _onchange_section_id(self):
        if not self.section_id:
            self.line_ids = [(5, 0, 0)]
            return
        enrollments = self.env['unisphere.enrollment'].search([
            ('section_id', '=', self.section_id.id),
            ('state', '=', 'enrolled'),
        ])
        lines = []
        for enr in enrollments:
            lines.append((0, 0, {
                'student_id': enr.student_id.id,
                'state': 'present',
                'remarks': '',
            }))
        self.line_ids = lines

    def action_save_attendance(self):
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_("No students found in the roster for this section!"))

        Attendance = self.env['unisphere.attendance']
        for line in self.line_ids:
            existing = Attendance.search([
                ('student_id', '=', line.student_id.id),
                ('section_id', '=', self.section_id.id),
                ('class_date', '=', self.class_date),
            ], limit=1)
            if existing:
                existing.write({
                    'state': line.state,
                    'remarks': line.remarks or existing.remarks,
                })
            else:
                Attendance.create({
                    'student_id': line.student_id.id,
                    'section_id': self.section_id.id,
                    'class_date': self.class_date,
                    'state': line.state,
                    'remarks': line.remarks or '',
                })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Attendance Recorded'),
                'message': _('Successfully saved session attendance for %d students.') % len(self.line_ids),
                'type': 'success',
                'sticky': False,
            }
        }


class UnisphereAttendanceWizardLine(models.TransientModel):
    _name = 'unisphere.attendance.wizard.line'
    _description = 'Attendance Entry Line'

    wizard_id = fields.Many2one('unisphere.attendance.wizard', required=True, ondelete='cascade')
    student_id = fields.Many2one('unisphere.student', string='Student', required=True, readonly=True)
    student_reg_no = fields.Char(related='student_id.student_id', string='Registration No', readonly=True)
    state = fields.Selection([
        ('present', 'Present'),
        ('late', 'Late'),
        ('absent', 'Absent'),
    ], string='Status', default='present', required=True)
    remarks = fields.Char(string='Remarks')
