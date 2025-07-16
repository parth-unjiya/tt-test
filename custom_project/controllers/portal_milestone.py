# -*- coding: utf-8 -*-
import base64
from datetime import datetime
from odoo import http, fields, _
from odoo.http import request


class MilestonePortal(http.Controller):

    @http.route(['/milestone/<int:milestone_id>'], type='http', auth='public', website=True, csrf=False)
    def portal_milestone_completion_form(self, milestone_id, access_token=None, **kw):
        milestone = request.env['milestone.completion.report'].sudo().search([
            ('id', '=', milestone_id),
            ('token', '=', access_token),
            ('token_expiry', '>=', fields.Datetime.now()),
            ('stage', '!=', 'accept')
        ], limit=1)

        if not milestone:
            return request.redirect('/milestone/token-invalid')

        return request.render('custom_project.portal_milestone_completion_form', {
            'milestone': milestone,
            'no_header': True,
            'no_footer': True
        })

    @http.route(['/milestone/sign/<int:milestone_id>'], type='json', auth='public', website=True)
    def portal_milestone_sign(self, milestone_id, access_token=None, name=None, signature=None):

        access_token = access_token or request.httprequest.args.get('access_token')
        print("access_token", access_token)
        milestone = request.env['milestone.completion.report'].sudo().search([
            ('id', '=', milestone_id),
            ('token', '=', access_token),
            ('token_expiry', '>=', fields.Datetime.now())
        ], limit=1)

        if not milestone:
            return {'error': 'Invalid or expired token'}

        if not signature:
            return {'error': 'Signature is missing'}


        milestone.write({
            'signature': signature,
            'signed_by': name,
            'signed_on': fields.Datetime.now(),
        })

        return {
            'force_refresh': True,
            'redirect_url': f'/milestone/{milestone_id}?access_token={access_token}&message=sign_ok'
        }

    @http.route(['/milestone/submit'], type='http', auth='public', website=True, csrf=True, methods=['POST'])
    def portal_milestone_completion_submit(self, **post):
        milestone_id = int(post.get('milestone_id'))
        token = post.get('access_token')

        milestone = request.env['milestone.completion.report'].sudo().search([
            ('id', '=', milestone_id),
            ('token', '=', token),
            ('token_expiry', '>=', fields.Datetime.now())
        ], limit=1)

        if not milestone:
            return request.redirect('/milestone/token-invalid')

        # Save client comment
        comment = post.get('client_comment', '').strip()
        if comment:
            milestone.client_comment = comment

        if milestone.signature:
            milestone.stage = 'accept'
            milestone.action_accept()
        else:
            milestone.stage = 'reject'
            milestone.action_reject()

        # Optional: mark milestone as submitted or update state
        milestone.message_post(
            body=_("Milestone reviewed by client. Comment and signature submitted."),
            message_type="comment"
        )

        milestone.project_id.message_post(
            body=_("Milestone reviewed by client. Comment and signature submitted."),   
            message_type="comment"
        )

        return request.redirect('/milestone/thank-you')

    @http.route('/milestone/thank-you', type='http', auth='public', website=True)
    def milestone_form_thank_you(self, **kw):
        return request.render('custom_project.portal_milestone_thank_you', {'no_header': True, 'no_footer': True})

    @http.route('/milestone/token-invalid', type='http', auth='public', website=True)
    def milestone_form_token_invalid(self, **kw):
        return request.render('custom_project.portal_milestone_token_invalid', {'no_header': True, 'no_footer': True})