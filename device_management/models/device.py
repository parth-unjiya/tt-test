from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta, MO, TU, WE, TH, FR, SA, SU


def get_next_wednesday(self):
    today = datetime.today()
    next_wed = today + relativedelta(weekday=WE(+1))
    return next_wed.replace(hour=12, minute=0, second=0, microsecond=0)


class Device(models.Model):
    _name = 'device.management'
    _description = 'Device Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char(string='Device Name', required=True, tracking=True)
    unique_name = fields.Char(string='Unique ID', tracking=True)
    tt_id = fields.Char(string="TT ID")
    device_label = fields.Char(string='Device Label', required=True, tracking=True)
    serial_number = fields.Char(string='Serial Number', tracking=True)
    imei_number = fields.Char(string='IMEI Number', tracking=True)

    device_type = fields.Selection([
        ('iphone', 'IPhone'),
        ('android', 'Android'),
        ('watch', 'Smart Watch')
    ], string='Device Type', required=True, tracking=True, default='iphone')

    category_id = fields.Many2one(
        'device.category',
        string='Device Category',
    )
    on_floor_date = fields.Date(string='On Floor Date', tracking=True)

    os_name = fields.Char(string='OS Name', tracking=True)
    os_version = fields.Char(string='OS Version', tracking=True)

    # Department and Location
    department_id = fields.Many2one('hr.department', string='Department', tracking=True)
    cabin_name = fields.Char(string='Cabin/Location', tracking=True)

    # Project Assignment
    project_name = fields.Char(string='Dedicated Project', tracking=True)

    # Device Status
    state = fields.Selection([
        ('on_floor', 'On Floor'),
        ('not_working', 'Not Working'),
        ('under_maintenance', 'Under Maintenance'),
        ('in_cabin', 'In Cabin'),
        ('spare', 'Spare'),
        ('sold', 'Sold'),
    ], string='Status', default='on_floor', tracking=True)

    order_state = fields.Integer(compute="_compute_order_state", store=True)

    @api.depends('state')
    def _compute_order_state(self):
        order_mapping = {
            'on_floor': 0,
            'not_working': 1,
            'under_maintenance': 2,
            'in_cabin': 3,
            'spare': 4,
            'sold': 5,
        }
        for record in self:
            record.order_state = order_mapping.get(record.state, 0)


    notes = fields.Html(string='Notes', tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    device_line_ids = fields.One2many('device.line', 'device_id', string='Device Lines')
    is_occupied = fields.Boolean(string='Is Occupied', default=False, tracking=True)
    occupied_by = fields.Many2one('res.users', string='Occupied By', tracking=True)

    @api.model_create_multi
    def create(self, vals):
        record = super(Device, self).create(vals)
        return record

    def action_mark_available(self):
        if not self.is_occupied:
            raise ValidationError(_("Device is already Available"))
        else:
            self.sudo().write({
                'is_occupied': False,
                'occupied_by': False,
            })
            device_line_object = self.env['device.line'].sudo().search([('device_id', '=', self.id)], order='id desc',
                                                                       limit=1)
            device_line_object.sudo().write({
                'is_occupied': False,
                'released_at': fields.Datetime.now(),
            })

    def action_mark_occupied(self):
        # user_id = self.env['res.users'].search([('id', '=', self.env.uid)], limit=1)
        user_id = self.env.uid
        if not self.is_occupied:
            self.sudo().write({
                'is_occupied': True,
                'occupied_by': user_id,
            })
            self.env['device.line'].sudo().create({
                'device_id': self.id,
                'is_occupied': True,
                'occupied_by': user_id,
                'occupied_at': fields.Datetime.now(),
                'status': 'occupied'
            })
        else:
            raise ValidationError(_("Device is already occupied"))

    @api.onchange('device_type')
    def _onchange_device_type(self):
        self.category_id = False
        return {'domain': {'category_id': [('device_type', '=', self.device_type)]}}



    def send_device_availability_email(self):
        # Sample logic to collect data
        devices = self.env['device.management'].search([('is_occupied', '=', False)])
        print("\nDebug-----------------------devices", devices)
        rm_group = self.env.ref('custom_dashboard.group_dashboard_operation_manager').id
        om_group = self.env.ref('custom_dashboard.group_dashboard_resource_manager').id
        ad_group = self.env.ref('custom_dashboard.group_dashboard_admin').id
        users = self.env['res.users'].search([('groups_id', 'in', [rm_group, om_group, ad_group])])
        print("\n\nDebug----------------------users", users)
        if not devices:
            return

        table_html = """
                <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%;">
                    <thead>
                        <tr style="background-color: #f2f2f2;">
                            <th>Device Name</th>
                            <th>Device Type</th>
                            <th>Device Label</th>
                            <th>Device Serial Number</th>
                            <th>Device IMEI Number</th>
                            <th>Device OS Name</th>
                            <th>Device OS Version</th>
                            <th>Device Status</th>
                        </tr>
                    </thead>
                    <tbody>
                """
        for device in devices:
            table_html += f"""
                        <tr>
                            <td>{device.name or ''}</td>
                            <td>{device.device_type or ''}</td>
                            <td>{device.category_id.name or ''}</td>
                            <td>{device.device_label or ''}</td>
                            <td>{device.serial_number or ''}</td>
                            <td>{device.imei_number or ''}</td>
                            <td>{device.os_name or ''}</td>
                            <td>{device.os_version or ''}</td>
                            <td>{dict(self._fields['state'].selection).get(device.state) or ''}</td>
                        </tr>
                    """
        table_html += """
                    </tbody>
                </table>
                """

        email_body = f"""
            <html>
                <head>
                    <style>
                        body {{
                            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                            font-size: 14px;
                            color: #333;
                            line-height: 1.6;
                        }}
                        table {{
                            width: 100%;
                            border-collapse: collapse;
                            margin-top: 20px;
                        }}
                        th, td {{
                            border: 1px solid #dddddd;
                            text-align: left;
                            padding: 8px;
                        }}
                        th {{
                            background-color: #f4f4f4;
                            color: #333;
                        }}
                        tr:nth-child(even) {{
                            background-color: #f9f9f9;
                        }}
                        p {{
                            margin: 10px 0;
                        }}
                    </style>
                </head>
                <body>
                    <p>Hello,</p>
                    <p>Here is the list of <strong>available devices</strong> as of <strong>{fields.Date.today().strftime('%Y-%m-%d')}</strong>:</p>
                    {table_html}
                    <p style="margin-top: 30px;">Regards,<br/><strong>Your Company</strong></p>
                </body>
            </html>
        """

        # Define the recipient
        if not users:
            raise UserError("Recipient not found.")

        # Send the email directly
        self.env['mail.mail'].create({
            'email_to': [record.partner_id.email for record in users],
            'subject': f'Device Availability Report - {fields.Date.today().strftime("%Y-%m-%d")}',
            'body_html': email_body,
            'auto_delete': True,
        }).send()


