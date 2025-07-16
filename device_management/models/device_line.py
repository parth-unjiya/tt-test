from odoo import models, fields, api
from datetime import datetime


class DeviceLine(models.Model):
    _name = 'device.line'
    _description = 'Device Management Lines'
    _rec_name = 'device_label'


    tt_id = fields.Char(string="TT ID")
    device_id = fields.Many2one('device.management', string='Device')
    device_label = fields.Char(string='Device Label', related='device_id.device_label')
    device_type = fields.Selection(string='Device Type', related='device_id.device_type')

    # Occupation Status
    is_occupied = fields.Boolean(string='Is Occupied', default=False)
    occupied_by = fields.Many2one('res.users', string='Occupied By')
    occupied_at = fields.Datetime(string='Occupied At')
    released_at = fields.Datetime(string='Released At')

    status = fields.Selection([
        ('occupied', 'Occupied'),
        ('available', 'Available'),
        ], string='Status')