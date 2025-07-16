from odoo import models, fields, api

class DeviceCategory(models.Model):
    _name = 'device.category'
    _description = 'Device Category'
    _order = 'device_type,name'

    name = fields.Char(string='Category Name', required=True)
    device_type = fields.Selection([
        ('mobile', 'Mobile'),
        ('tablet', 'Tablet'),
        ('watch', 'Smart Watch')
    ], string='Device Type', required=True)
    active = fields.Boolean(default=True)
    description = fields.Text(string='Description')

    _sql_constraints = [
        ('unique_category_name_type', 
         'UNIQUE(name, device_type)',
         'Category name must be unique per device type!')
    ] 