from odoo import api, fields, models

class DeviceManagement(models.Model):
    _name = 'device.management'
    _inherit = ['device.management']  # Keep your existing inheritance

    # Computed fields for dashboard
    total_count = fields.Integer(string='Total Devices', compute='_compute_device_counts')
    available_count = fields.Integer(string='Available Devices', compute='_compute_device_counts')
    occupied_count = fields.Integer(string='Occupied Devices', compute='_compute_device_counts')
    
    mobile_count = fields.Integer(string='Mobile Devices', compute='_compute_device_type_counts')
    tablet_count = fields.Integer(string='Tablets', compute='_compute_device_type_counts')
    other_count = fields.Integer(string='Other Devices', compute='_compute_device_type_counts')
    
    department_distribution = fields.Json(string='Department Distribution', compute='_compute_department_distribution')

    @api.depends('state')
    def _compute_device_counts(self):
        for record in self:
            domain = []
            record.total_count = self.search_count(domain)
            record.available_count = self.search_count([('state', '=', 'available')])
            record.occupied_count = self.search_count([('state', '=', 'occupied')])

    @api.depends('device_type')
    def _compute_device_type_counts(self):
        for record in self:
            record.mobile_count = self.search_count([('device_type', '=', 'mobile')])
            record.tablet_count = self.search_count([('device_type', '=', 'tablet')])
            record.other_count = self.search_count([
                ('device_type', 'not in', ['mobile', 'tablet'])
            ])

    @api.depends('department_id')
    def _compute_department_distribution(self):
        for record in self:
            # Group devices by department
            departments = self.read_group(
                [],
                ['department_id'],
                ['department_id']
            )
            
            data = {
                'labels': [],
                'datasets': [{
                    'data': [],
                    'backgroundColor': []
                }]
            }
            
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
            
            for idx, dept in enumerate(departments):
                if dept['department_id']:
                    name = dept['department_id'][1]
                    count = dept['department_id_count']
                    data['labels'].append(name)
                    data['datasets'][0]['data'].append(count)
                    data['datasets'][0]['backgroundColor'].append(colors[idx % len(colors)])
            
            record.department_distribution = data 