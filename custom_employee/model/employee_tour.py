from odoo import fields, models, api, tools, _
from datetime import datetime, timedelta


class CustomCRMLead(models.Model):
    _name = 'hr.employee.tour'
    _description = 'Employee Tour Data'

    tt_id = fields.Char(string="TT ID")
    employee_id = fields.Many2one('hr.employee', string="Employee")
    start_date = fields.Datetime(string="Start Date")
    end_date = fields.Datetime(string="End Date")
    tour_status = fields.Selection([('active', 'Active'),
                                      ('inactive', 'Inactive')], string="Tour Status")
    description = fields.Text(string="Description")
