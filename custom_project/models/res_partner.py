from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = "res.partner"

    tt_id = fields.Char(string="TT ID")
    skype = fields.Char(string="Skype")
    gmail = fields.Char(string="Gmail")
    slack = fields.Char(string="Slack")
    crm_partner_id = fields.Char(string="CRM Partner ID")
