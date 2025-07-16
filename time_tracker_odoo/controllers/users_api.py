import json
import logging
import secrets
import werkzeug
from datetime import datetime, timedelta
from odoo import http, api, SUPERUSER_ID
from odoo.http import request
from odoo.exceptions import AccessDenied
from werkzeug.wrappers import Response


_logger = logging.getLogger(__name__)


class SearchApi(http.Controller):

    @http.route("/user/get-departments", type="http", auth="api_key", methods=["GET"], csrf=False)
    def _get_department(self, **kwargs):
        name = kwargs.get("keyword")
        try:
            department_id = request.env['hr.department'].sudo().search([("name", "ilike", f"%{name}%")])
            data = {
                "responseCode": 200,
                "responseMessage": "success",
                "responseData": [
                    {
                        "id": department.id,
                        "name": department.name,
                    } for department in department_id
                ]
            }
            _logger.info("Department Got from Search: %s", department_id)
            return json.dumps(data)
        except Exception as e:
            data = {
                "responseCode": 400,
                "responseMessage": "error",
                "responseData": []
            }
            _logger.error(e)
        return json.dumps(data)


    @http.route("/user/get-developers", type="http", auth="api_key", methods=["GET"], csrf=False)
    def _get_developers(self, **kwargs):

        name = kwargs.get("keyword")
        try:
            user_id = request.env['res.users'].sudo().search([("name", "ilike", f"%{name}%")])
            data = {
                "responseCode": 200,
                "responseMessage": "success",
                "responseData": [
                    {
                        "id": record.id,
                        "name": record.name,
                    } for record in user_id
                ]
            }
            _logger.info("User Got from Search: %s", user_id)
            return json.dumps(data)
        except Exception as e:
            data = {
                "responseCode": 400,
                "responseMessage": "error",
                "responseData": []
            }
            _logger.error(e)
        return json.dumps(data)


    # @http.route("/user/get-project-managers", type="http", auth="api_key", methods=["GET"], csrf=False)
    # def _get_managers(self, **kwargs):

    #     name = kwargs.get("keyword")
    #     try:
    #         user_id = request.env['res.users'].sudo().search([("name", "ilike", f"%{name}%")])
    #         data = {
    #             "responseCode": 200,
    #             "responseMessage": "success",
    #             "responseData": [
    #                 {
    #                     "id": user.id,
    #                     "name": user.name,
    #                 } for user in user_id
    #             ]
    #         }
    #         _logger.info("Manager Got from Search: %s", user_id)
    #         return json.dumps(data)
    #     except Exception as e:
    #         data = {
    #             "responseCode": 400,
    #             "responseMessage": "error",
    #             "responseData": []
    #         }
    #         _logger.error(e)
    #         return json.dumps(data)

    @http.route("/user/search-developers", type="http", auth="api_key", methods=["POST"], csrf=False)
    def _get_users(self, **kwargs):

        name = kwargs.get("keyword")
        try:
            user_id = request.env['res.users'].sudo().search([("name", "ilike", f"%{name}%")])
            data = {
                "responseCode": 200,
                "responseMessage": "success",
                "responseData": [
                    {
                        "id": record.id,
                        "name": record.name,
                    }
                    for record in user_id]
            }
            _logger.info("User Got from Search: %s", user_id)
            return json.dumps(data)
        except Exception as e:
            data = {
                "responseCode": 400,
                "responseMessage": "error",
                "responseData": []
            }
            _logger.error(e)
            return json.dumps(data)
