# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class TicketSearch(http.Controller):
    @http.route(['/ticketsearch'], type='json', auth="public", website=True)
    def ticket_search(self, **kwargs):
        """
        Search for tickets based on the provided search value.
        :param search_value: The value to search for in the ticket name or subject.
        :type search_value: str
        :return: A JSON response containing the matching tickets.
        :rtype: http.Response
        """
        search_value = kwargs.get("search_value")
        tickets = request.env["ticket.helpdesk"].search(
            ['&', ('employee_id', '=', request.env.user.partner_id.id), '|', ('name', 'ilike', search_value),
             ('ticket_sequence', 'ilike', search_value)],)
        values = {
            'tickets': tickets,
        }
        response = http.Response(template='odoo_website_helpdesk.ticket_table',
                                 qcontext=values)
        return response.render()
