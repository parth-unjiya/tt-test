# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _


class LostReason(models.Model):
    _name = "ticket.cancel.reason"
    _description = 'Ticket Cancel Reason'

    name = fields.Char('Description', required=True, translate=True)
    active = fields.Boolean('Active', default=True)
    tickets_count = fields.Integer('Ticket Count', compute='_compute_tickets_count')

    def _compute_tickets_count(self):
        ticket_data = self.env['ticket.helpdesk'].with_context(active_test=False)._read_group(
            [('cancel_reason_id', 'in', self.ids)],
            ['cancel_reason_id'],
            ['__count'],
        )
        mapped_data = {lost_reason.id: count for lost_reason, count in ticket_data}
        for reason in self:
            reason.tickets_count = mapped_data.get(reason.id, 0)

    def action_cancel_tickets(self):
        return {
            'name': _('Tickets'),
            'view_mode': 'tree,form',
            'domain': [('cancel_reason_id', 'in', self.ids)],
            'res_model': 'ticket.helpdesk',
            'type': 'ir.actions.act_window',
            'context': {'create': False, 'active_test': False},
        }
