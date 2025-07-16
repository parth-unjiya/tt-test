# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome


class AutoLoginController(AuthSignupHome):

    @http.route()
    def web_login(self, *args, **kw):
        """Override the login route to add custom session handling."""

        response = super().web_login(*args, **kw)
        remember_me = kw.get("remember_me") == "on"

        if request.session.uid and remember_me:
            # Set session lifetime to 30 days
            http.SESSION_LIFETIME = 60 * 60 * 24 * 30
            request.future_response.set_cookie(
                "session_id",
                request.session.sid,
                max_age=http.SESSION_LIFETIME,
                httponly=True,
            )

        elif request.session.uid and not remember_me:
            # Set session lifetime to 1 day
            http.SESSION_LIFETIME = 60 * 60 * 24 * 1
            request.future_response.set_cookie(
                "session_id",
                request.session.sid,
                max_age=http.SESSION_LIFETIME,
                httponly=True,
            )

        return response
