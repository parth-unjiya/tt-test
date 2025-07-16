# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MergeTicket(models.Model):
    """Tickets merging class"""
    _name = 'merge.ticket'
    _description = 'Merging the selected tickets'
    _rec_name = 'support_ticket_id'

    user_id = fields.Many2one('res.partner',
                              string='Responsible User',
                              help='User name of responsible person.',
                              default=lambda self: self.env.user.partner_id.id)
    support_team_id = fields.Many2one('team.helpdesk',
                                      string='Support Team',
                                      help='Name of the support team.')
    employee_id = fields.Many2one('res.partner', string='Employee',
                                  help='Name of the Employee ')
    support_ticket_id = fields.Many2one('ticket.helpdesk',
                                        string='Support Ticket',
                                        help="Name of the support ticket")
    new_ticket = fields.Boolean(string='Create New Ticket ?',
                                help='Creating new tickets or not.',
                                default=False)
    subject = fields.Char(string='Subject', help='Enter the New Ticket Subject')
    merge_reason = fields.Char(string='Merge Reason',
                               help='Reason for Merging the tickets. ')
    support_ticket_ids = fields.One2many('support.ticket',
                                         'support_ticket_id',
                                         string='Support Tickets',
                                         help='Merged tickets')
    active = fields.Boolean(string='Disable Record', help='Disable Record',
                            default=True)

    def default_get(self, fields_list):
        """Override the default_get method to provide default values for fields
        when creating a new record."""
        defaults = super(MergeTicket, self).default_get(fields_list)
        active_ids = self._context.get('active_ids', [])
        selected_tickets = self.env['ticket.helpdesk'].browse(active_ids)
        employee_ids = selected_tickets.mapped('employee_id')
        subjects = selected_tickets.mapped('name')
        display_names = selected_tickets.mapped('display_name')
        helpdesk_team = selected_tickets.mapped('team_id')
        descriptions = selected_tickets.mapped('description')
        if len(employee_ids):
            defaults.update({
                'employee_id': employee_ids[0].id,
                'support_team_id': helpdesk_team,
                'support_ticket_ids': [(0, 0, {
                    'subject': subject,
                    'display_name': display_name,
                    'description': description,
                }) for subject, display_name, description in
                                       zip(subjects, display_names,
                                           descriptions)]
            })
        return defaults

    def action_merge_ticket(self):
        """Merging the tickets or creating new tickets"""
        if self.new_ticket:
            description = "\n\n".join(
                f"{ticket.name}\n{'-' * len(ticket.name)}\n{ticket.description}"
                for ticket in self.support_ticket_ids
            )
            self.env['ticket.helpdesk'].create({
                'name': self.name,
                'description': description,
                'employee_id': self.employee_id.id,
                'team_id': self.support_team_id.id,
            })
        else:
            print("\nDebug--------------------- support_ticket_ids --------------->", self.support_ticket_ids)
            if len(self.support_ticket_ids):
                description = "\n\n".join(
                    f"{ticket.display_name}\n{'-' * len(ticket.display_name)}\n{ticket.description}"
                    for ticket in self.support_ticket_ids
                )
                self.support_ticket_id.write({
                    'description': description,
                    'merge_ticket_invisible': True,
                    'merge_count': len(self.support_ticket_ids),
                })

    @api.onchange('support_ticket_id')
    def _onchange_support_ticket_id(self):
        """Onchange function to add the support ticket id."""
        self.support_ticket_ids.write({
            'merged_ticket': self.support_ticket_id
        })
