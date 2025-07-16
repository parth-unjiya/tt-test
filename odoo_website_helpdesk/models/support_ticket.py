# -*- coding: utf-8 -*-

from odoo import fields, models


class SupportTicket(models.Model):
    """Creating onetoMany model"""
    _name = 'support.ticket'
    _description = 'Support Tickets'

    subject = fields.Char(string='Subject', help='Subject of the merged '
                                                 'tickets.')
    display_name = fields.Char(string='Display Name',
                               help='Display name of the merged tickets.')
    description = fields.Char(string='Description',
                              help='Description of the tickets.')
    support_ticket_id = fields.Many2one('merge.ticket',
                                        string='Support Tickets',
                                        help='Support tickets')
    merged_ticket = fields.Integer(string='Merged Ticket ID',
                                   help='Storing merged ticket id')
