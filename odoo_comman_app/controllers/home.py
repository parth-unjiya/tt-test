# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.home import Home as WebHome


class Home(WebHome):

    @http.route()
    def index(self, *args, **kw):
        print("DEBUG: ********* Home index *********")
        if not request.session.uid:
            url = request.env["ir.config_parameter"].sudo().get_param("landing_pages_url")
            print("DEBUG URL: ", url)
            if not url:
                url = "/web/login"
            return request.redirect(url)
        return super().index(*args, **kw)
