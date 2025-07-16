# -*- coding: utf-8 -*-

from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        result = super(IrHttp, self).session_info()
        config_parameter = request.env["ir.config_parameter"].sudo()
        result["web_title"] = config_parameter.get_param("web_title", "Space-O")
        result['app_show_footer'] = config_parameter.get_param('app_show_footer')
        result['header_social_links'] = config_parameter.get_param('header_social_links')
        result['header_call_to_action'] = config_parameter.get_param('header_call_to_action')
        result['header_text_element'] = config_parameter.get_param('header_text_element')
        result['header_search_box'] = config_parameter.get_param('header_search_box')
        result['landing_pages_url'] = config_parameter.get_param('landing_pages_url')
        return result
