# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class TicketGroupBy(http.Controller):
    """Controller for handling ticket grouping based on different criteria."""

    @http.route(['/ticketgroupby'], type='json', auth="public", website=True)
    def ticket_group_by(self, **kwargs):
        """grouping tickets based on user-defined criteria.
        Args:
        - kwargs (dict): Keyword arguments received from the HTTP request.
        Returns:
        - http.Response: Rendered HTTP response containing grouped ticket information.
        """
        context = []
        group_value = kwargs.get("search_value")
        if group_value == '0':
            context = []
            tickets = request.env["ticket.helpdesk"].search(
                [('user_id', '=', request.env.user.id)])
            if tickets:
                context.append({
                    'name': '',
                    'data': tickets
                })
        if group_value == '1':
            context = []
            stage_ids = request.env['ticket.stage'].search([])
            for stage in stage_ids:
                ticket_ids = request.env['ticket.helpdesk'].search([
                    ('stage_id', '=', stage.id),
                    ('user_id', '=', request.env.user.id)
                ])
                if ticket_ids:
                    context.append({
                        'name': stage.name,
                        'data': ticket_ids
                    })
        if group_value == '2':
            context = []
            type_ids = request.env['helpdesk.type'].search([])
            for types in type_ids:
                ticket_ids_1 = request.env['ticket.helpdesk'].search([
                    ('ticket_type_id', '=', types.id),
                    ('user_id', '=', request.env.user.id)
                ])
                if ticket_ids_1:
                    context.append({
                        'name': types.name,
                        'data': ticket_ids_1
                    })
        values = {
            'tickets': context,
        }
        response = http.Response(
            template='odoo_website_helpdesk.ticket_group_by_table',
            qcontext=values)
        return response.render()


class HelpdeskController(http.Controller):

    @http.route('/helpdesk/ticket/view', type='http', auth="public", website=True)
    def view_ticket(self, data_id, **kwargs):
        """View Ticket Page for External Users"""
        try:
            data_id = int(data_id)
        except ValueError:
            data_id = data_id.split('_')[1]
        print("------------------called-------------------", data_id)
        ticket = request.env['ticket.helpdesk'].sudo().search([
            ('id', '=', int(data_id))])
        print("--------------ticket", ticket)

        if not ticket:
            return request.not_found()

        user_lang = ticket.employee_id.lang or request.env.user.lang
        company = ticket.create_uid.company_id

        # Redirect internal users to backend form view
        if request.session.uid and request.env.user.has_group('base.group_user'):
            return request.redirect(
                '/web?db=%s#id=%s&view_type=form&model=ticket.helpdesk' % (request.env.cr.dbname, data_id))

        # Render custom ticket page for external users
        response_content = request.env['ir.ui.view'].with_context(lang=user_lang)._render_template(
            'auth_signup.login', {  # Use your actual template name
                'company': company,
                'ticket': ticket,
            })
        return request.make_response(response_content, headers=[('Content-Type', 'text/html')])

