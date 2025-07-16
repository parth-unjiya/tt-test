# -*- coding: utf-8 -*-

from odoo import http
from odoo.addons.web.controllers.session import Session


class SessionWebsite(Session):

    @http.route('/web/session/logout', website=True, multilang=False, sitemap=False)
    def logout(self, redirect='/web'):
        print("\n\nDEBUG: **********Logout**********")
        redirect = '/web/login'
        print(f"DEBUG: redirect = {redirect}")
        return super().logout(redirect=redirect)