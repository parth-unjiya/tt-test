from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    update_traker = fields.Char(string="Update Traker", config_parameter="time_tracker_odoo.update_traker")
