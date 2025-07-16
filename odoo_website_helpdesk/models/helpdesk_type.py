# -*- coding: utf-8 -*-
from odoo import fields, models


class HelpdeskType(models.Model):
    """Helpdesk type """
    _name = 'helpdesk.type'
    _description = 'Helpdesk Type'

    name = fields.Char(string='Type', help='Types of help desk.')

    team_ids = fields.Many2many(
        'team.helpdesk',
        relation='ticket_type_team_rel',
        column1='type_id',
        column2='team_id',
        string='Teams'
    )
