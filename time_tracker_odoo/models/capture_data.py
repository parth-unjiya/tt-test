from odoo import models, fields


class CaptureData(models.Model):
    _name = "capture.data"
    _description = "Captured Data"
    _order = "id desc"

    capture_type = fields.Integer(string="Capture Type", required=True) # 1 for screenshot 2 for keyword 4 mouse movement
    capture_data = fields.Text(string="Capture Data", required=True)
    user_id = fields.Many2one("res.users", string="User", required=True)
    machinedetail = fields.Char(string="Machine Detail", size=20)
    time_tracking_application_id = fields.Integer(string="Time Tracking App ID")
    creation_time = fields.Char(string="Creation Time")


class InfringementInfo(models.Model):
    _name = 'infringement.info'
    _description = 'Infringement Info'

    type_id = fields.Integer()
    infregment_time = fields.Char()
    machinedetail = fields.Char()
    user_id = fields.Many2one('res.users')

    # Infringement Type
    # 1 for social media access 
    # 2 for restricted website access 
    # 3 for pendrive/unatuhorise device access like external HDD 
    # 4 Bluetooth access 
    # 5 Tethering connection access