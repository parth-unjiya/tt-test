from odoo import fields, models, api, tools, _
from datetime import datetime, timedelta


class CustomCRMLead(models.Model):
    _name = 'hr.employee.promotion'
    _description = 'Employee Promotion Data'

    tt_id = fields.Char(string="TT ID")
    employee_id = fields.Many2one('hr.employee', string="Employee")
    start_date = fields.Datetime(string="Start Date")
    end_date = fields.Datetime(string="End Date")
    department_id = fields.Many2one('hr.department',string="Department")
    job_id = fields.Many2one('hr.job',string="Job Position")