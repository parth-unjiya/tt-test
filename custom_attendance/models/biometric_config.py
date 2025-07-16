# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    biometric_server = fields.Char(
        string="SQL Server IP",
        config_parameter="biometric.server",
        default="172.16.17.167:1433",
    )
    biometric_user = fields.Char(
        string="SQL Server User", 
        config_parameter="biometric.user",
        default="sa",
    )
    biometric_password = fields.Char(
        string="SQL Server Password",
        config_parameter="biometric.password",
        default="Spaceo@123",
    )
    biometric_database = fields.Char(
        string="SQL Database Name",
        config_parameter="biometric.database",
        default="UNIVERSAL",
    )
