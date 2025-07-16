# -*- coding: utf-8 -*-

from odoo import fields, models


class HelpdeskTag(models.Model):
    """Helpdesk tags"""
    _name = 'helpdesk.tag'
    _description = 'Helpdesk Tags'

    name = fields.Char(string='Tag', help='Tag name of the helpdesk.')
