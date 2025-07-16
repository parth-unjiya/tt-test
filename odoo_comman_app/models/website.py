from odoo import api, fields, models, tools, _


class Website(models.Model):
    _inherit = "website"

    logo_redirect_url = fields.Char(
        string="Logo Redirect URL",
        help="Redirect URL when user click on logo",
    )
    