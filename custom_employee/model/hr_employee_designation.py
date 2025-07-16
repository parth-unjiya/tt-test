from odoo import fields, models, api, tools, _
from datetime import datetime, timedelta


class HRDesignation(models.Model):
    _name = 'hr.employee.designation'
    _description = 'Employee Designation'

    tt_id = fields.Char(string="TT ID")
    name = fields.Char(string="Designation")
    short_name = fields.Char(string="Short Name")
    department_id = fields.Many2one('hr.department', string="Department")
    active = fields.Boolean(string="Active", default=True)


class HRSubDesignation(models.Model):
    _name = 'hr.employee.sub.designation'
    _description = 'Employee Sub Designation'

    tt_id = fields.Char(string="TT ID")
    name = fields.Char(string="Sub Designation")
    designation_id = fields.Many2one('hr.employee.designation', string="Designation")
    department_id = fields.Many2one('hr.department', string="Department")
    active = fields.Boolean(string="Active", default=True)


class HRCustomJobPosition(models.Model):
    _inherit = 'hr.job'

    tt_id = fields.Char(string="TT ID")
    designation_id = fields.Many2one('hr.employee.designation', string="Designation")
    sub_designation_id = fields.Many2one('hr.employee.sub.designation', string="Sub Designation")
    helpdesk_support_manager_ids = fields.Many2many('res.users', 'hr_job_ticket_rel', string="Helpdesk Support Manager")



class HRCustomContract(models.Model):
    _inherit = 'hr.contract'

    designation_id = fields.Many2one('hr.employee.designation', string="Designation")
    sub_designation_id = fields.Many2one('hr.employee.sub.designation', string="Sub Designation")
    document_ids = fields.Many2many(
        'document.template',
        'contract_template_rel',
        'contract_id',
        'template_id',
        string='Document Templates'
    )

    def action_open_document_wizard(self):
        self.ensure_one()
        return {
            'name': 'Generate Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'contract.document.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_contract_id': self.id
            }
        }

