# -*- coding: utf-8 -*-

from odoo import http, fields
from odoo.http import request
from datetime import datetime


class ProjectAcceptancePortal(http.Controller):

    @http.route(['/project/acceptance/<int:report_id>'], type='http', auth='public', website=True, csrf=False)
    def portal_acceptance_report(self, report_id, access_token=None, **kw):
        report = request.env['project.acceptance.report'].sudo().search([
            ('id', '=', report_id),
            ('token', '=', access_token),
            ('stage', '!=', 'accept'),
            ('token_expiry', '>=', fields.Datetime.now())
        ], limit=1)

        if not report:
            return request.redirect('/project/acceptance/token-invalid')

        return request.render('custom_project.portal_acceptance_report_form', {
            'report': report,
            'no_header': True,
            'no_footer': True
        })

    @http.route(['/project/acceptance/submit'], type='http', auth='public', website=True, methods=['POST'], csrf=True)
    def portal_acceptance_submit(self, **post):
        report_id = int(post.get('report_id'))
        token = post.get('access_token')

        report = request.env['project.acceptance.report'].sudo().search([
            ('id', '=', report_id),
            ('token', '=', token),
            ('stage', '!=', 'accept'),
        ], limit=1)

        if not report:
            return request.redirect('/project/acceptance/token-invalid')

        # Save client comment
        report.note = post.get('client_comment', '').strip()

        # Check if signed
        if report.client_signature:
            report.stage = 'accept'
            report.action_accept()
        else:
            report.stage = 'reject'
            report.action_reject()

        report.project_id.message_post(
            body=f"Client submitted the acceptance form. Status: {report.stage.title()}.",
            message_type="comment"
        )

        return request.redirect('/project/acceptance/thank-you')


    @http.route(['/project/acceptance/sign/<int:report_id>'], type='json', auth='public', website=True)
    def portal_acceptance_sign(self, report_id, access_token=None, name=None, signature=None):
        access_token = access_token or request.httprequest.args.get('access_token')

        report = request.env['project.acceptance.report'].sudo().search([
            ('id', '=', report_id),
            ('token', '=', access_token)
        ], limit=1)

        if not report or not signature:
            return {'error': 'Invalid token or missing signature.'}

        report.write({
            'client_signed_by': name,
            'client_signed_on': fields.Date.today(),
            'client_signature': signature
        })

        return {
            'force_refresh': True,
            'redirect_url': f'/project/acceptance/{report_id}?access_token={access_token}&message=sign_ok'
        }


    @http.route('/project/acceptance/thank-you', type='http', auth='public', website=True)
    def milestone_form_thank_you(self, **kw):
        return request.render('custom_project.portal_acceptance_thank_you', {'no_header': True, 'no_footer': True})

    @http.route('/project/acceptance/token-invalid', type='http', auth='public', website=True)
    def milestone_form_token_invalid(self, **kw):
        return request.render('custom_project.portal_acceptance_token_invalid', {'no_header': True, 'no_footer': True})