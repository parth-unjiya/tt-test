# -*- coding: utf-8 -*-
from odoo import fields, models


class HelpdeskCategory(models.Model):
    """Category Model"""
    _name = 'helpdesk.category'
    _description = 'Categories'


    tt_id = fields.Char('TT ID')
    name = fields.Char('Name', help='Category name of the helpdesk')
    sequence = fields.Integer('Sequence', default=0,
                              help='Sequence of the helpdesk category')
    active = fields.Boolean('Active', default=True)
    designation_id = fields.Many2one('hr.job', string='Department')
