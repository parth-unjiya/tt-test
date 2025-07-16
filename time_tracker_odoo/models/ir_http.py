# Copyright 2018 ACSONE SA/NV
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import models
from odoo.exceptions import AccessDenied
from odoo.http import request

_logger = logging.getLogger(__name__)


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _auth_method_api_key(cls):
        """Authenticate API requests using Bearer Token in Authorization header"""

        headers = request.httprequest.headers
        auth_header = headers.get("Authorization")

        if auth_header and auth_header.startswith("Bearer "):
            api_key = auth_header.split(" ")[1]  # Extract API key

            request.update_env(user=1)
            auth_api_key = request.env["auth.api.key"]._retrieve_api_key(api_key)

            if auth_api_key:
                # Reset _env on the request since we change the user
                request._env = None
                request.update_env(user=auth_api_key.user_id.id)

                # Store authentication details in the request
                request.auth_api_key = api_key
                request.auth_api_key_id = auth_api_key.id
                return True

        _logger.error("Invalid Authorization header, access denied")
        raise AccessDenied()
