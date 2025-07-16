from odoo import models, fields

class WebsiteMenu(models.Model):
    _inherit = 'website.menu'

    user_group_ids = fields.Many2many('res.groups', string='Visible Groups') 