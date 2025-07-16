# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request


class WebsiteView(http.Controller):
    """Inherited http.Controller to add custom route"""

    @http.route('/public/survey', type='http', auth="public",
                website=True)
    def public_user_access(self):
        """ Controller function to access survey from website """
        survey = request.env['survey.survey'].sudo().search(
            [('access_mode', '=', 'website')])
        values = {
            'survey_list': [{
                'title': rec.title,
                'attempts': rec.attempts_limit,
                'date': rec.create_date,
                'access_token': rec.access_token
            } for rec in survey],
        }
        return request.render("enhanced_survey_management.survey_visibility",
                              values)
