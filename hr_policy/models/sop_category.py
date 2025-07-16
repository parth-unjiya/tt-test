from odoo import models, fields, api,exceptions


class SopCategory(models.Model):
    _name = "sop.category"
    _description = "Sop Category"

    name = fields.Char('Name')