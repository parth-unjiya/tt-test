# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    bd_token = fields.Char(
        "Bright Data Token",
        help="Token for fetching LinkedIn data",
        config_parameter="custom_recruitment.bd_token",
    )

    bd_dataset_id = fields.Char(
        "Bright Data Dataset ID",
        help="Dataset ID for LinkedIn data",
        config_parameter="custom_recruitment.bd_dataset_id",
    )

    to_emails_recruitment = fields.Char(
        string="Default To Emails For Recruitment",
        config_parameter="custom_recruitment.to_emails_recruitment",
        help="Comma-separated list of To emails (e.g., management@example.com, director@example.com)"
    )

    cc_emails_recruitment = fields.Char(
        string="Default CC Emails For Recruitment",
        config_parameter="custom_recruitment.cc_emails_recruitment",
        help="Comma-separated list of To emails (e.g., management@example.com, director@example.com)"
    )

    to_emails_management = fields.Char(
        string="To Emails For Upper Management",
        config_parameter="custom_recruitment.to_emails_upper_management",
        help="Comma-separated list of To emails (e.g., management@example.com, director@example.com)"
    )



class CustomRESUsers(models.Model):
    _inherit = 'res.users'

    tt_id = fields.Char(string="TT ID")


class CustomDepartment(models.Model):
    _inherit = 'hr.department'

    tt_id = fields.Char(string="TT ID")