import json

from odoo import http
from odoo.http import request
from datetime import datetime

import base64
import io
from odoo import http
from PIL import Image


def get_employee_image(employee_id):
    if employee_id.image_128:  # Check if the employee has an image
        image_data = base64.b64decode(employee_id.image_128)  # Decode base64 image
        image = Image.open(io.BytesIO(image_data))  # Open image with PIL

        # Convert to PNG
        img_io = io.BytesIO()
        image.save(img_io, format='PNG')
        img_io.seek(0)

        # Encode to base64 again for storing
        png_base64 = base64.b64encode(img_io.read()).decode('utf-8')

        attachment = employee_id.env['ir.attachment'].search([('res_model', '=', 'hr.employee'),
                                                              ('res_id', '=', employee_id.id), ('name', '=', f'employee_{employee_id.id}.png')])
        if attachment:
            return f"http://172.16.17.64:6767/web/image/ir.attachment/{attachment.id}/datas/{attachment.name}"
        else:
            # Create an attachment to store the PNG image in Odoo
            attachment = employee_id.env['ir.attachment'].create({
                'name': f'employee_{employee_id.id}.png',
                'type': 'binary',
                'datas': png_base64,
                'mimetype': 'image/png',
                'res_model': 'hr.employee',
                'res_id': employee_id.id,
                'public': True
            })
            print("---------------attachment", attachment)
            return f"http://172.16.17.64:6767/web/content/{attachment.id}/employee_{employee_id.id}.png"

    return False  # No image available


class DeviceManagement(http.Controller):

    @http.route('/device_occupied', auth='public', methods=['POST', 'GET'], type='http', csrf=False)
    def device_occupied(self, **kwargs):
        """
        Handle requests to check if a device is occupied.

        This method processes HTTP POST and GET requests to determine if a device, identified
        by a unique name provided in the request, is associated with an employee based on the
        employee code. It prints debugging information and checks if the employee is an HR desk
        employee to determine further actions.

        :param kwargs: A dictionary containing request parameters, including:
            - 'vEmployeeCode': The code of the employee (str).
            - 'vUniqueId': The unique name of the device (str).
        :return: A JSON response indicating the success or failure of the operation.
        """
        print("---------------------------", kwargs)
        employee_id = request.env['hr.employee'].sudo().search([('emp_code', '=', kwargs.get('vEmployeeCode'))], limit=1)
        device_object = request.env['device.management'].sudo().search([('unique_name', '=', kwargs.get('vUniqueId'))])
        print("------------------device_object", device_object)
        base_url = request.env["ir.config_parameter"].sudo().get_param("web.base.url")
        if employee_id:
            if not employee_id.is_hr_desk:
                print("\nDebug ------------------------------------ IN IF CONDITION -------------------------------------------")
                user_id = employee_id.user_id
                print("------------------user_id", user_id)
                device_object.sudo().write({
                    'is_occupied': True,
                    'occupied_by': user_id,
                })
                line_item = device_object.env['device.line'].sudo().create({
                    'device_id': device_object.id,
                    'is_occupied': True,
                    'occupied_by': user_id.id,
                    'occupied_at': datetime.now(),
                    'status': 'occupied'
                })
                response_data = {
                    "vEmployeeCode": employee_id.emp_code,
                    "vFirstName": employee_id.name.split(" ")[0] if employee_id.name.split(" ")[
                        0] else employee_id.name,
                    "vLastName": employee_id.name.split(" ")[1] if employee_id.name.split(" ")[1] else False,
                    "vProfileImage": get_employee_image(employee_id),
                    "iBookingTime": int(line_item.occupied_at.strftime("%Y%m%d%H%M%S")),
                    "iSpentTime": 0
                }
                print("\n\nresponse_data---------------", response_data)
                return json.dumps({
                    "responseCode": 200,
                    "responseMessage": "Success",
                    "responseData": response_data
                })
            else:
                print("\nDebug ------------------------------------ IN ELSE CONDITION -------------------------------------------")
                device_object.sudo().write({
                    'is_occupied': False,
                    'occupied_by': False,
                })
                device_line_object = request.env['device.line'].sudo().search([('device_id', '=', device_object.id)], order='id desc', limit=1)
                line_item = device_line_object.sudo().write({
                    'is_occupied': False,
                    'released_at': datetime.now(),
                })
                total_minutes = (device_line_object.released_at - device_line_object.occupied_at).total_seconds() // 60
                response_data = {
                    "vEmployeeCode": employee_id.emp_code,
                    "vFirstName": employee_id.name.split(" ")[0] if employee_id.name.split(" ")[0] else employee_id.name,
                    "vLastName": employee_id.name.split(" ")[1] if employee_id.name.split(" ")[1] else False,
                    "vProfileImage": get_employee_image(employee_id),
                    "iBookingTime": int(device_line_object.occupied_at.strftime("%Y%m%d%H%M%S")),
                    "iSpentTime": int(total_minutes)
                }
                print("\n\nresponse_data---------------", response_data)
                return json.dumps({
                    "responseCode": 200,
                    "responseMessage": "Success",
                    "responseData": response_data
                })
        else:
            return {
                "responseCode": 400,
                "responseMessage": "Invalid QR code. Please scan with correct QR code.",
                "responseData": []
            }



class UserAuthAPI(http.Controller):

    @http.route('/odoo/api/v1/auth/login', type='json', auth='none', methods=['POST','GET'], csrf=False)
    def authenticate_user(self, **kwargs):
        """ Authenticate user and create a session. """

        print("----------------------->", kwargs)
        db = request.env.cr.dbname
        login = kwargs.get('login')
        password = kwargs.get('password')

        if not login or not password:
            return {'status': 'error', 'message': 'Missing login or password'}

        try:
            # Authenticate user
            uid = request.env['res.users'].sudo().authenticate(db, login, password, {})
            if not uid:
                return {'status': 'error', 'message': 'Invalid credentials'}

            # Start session
            request.session.authenticate(db, login, password)

            # Fetch user data
            user = request.env['res.users'].sudo().browse(uid)
            return {
                'status': 'success',
                'username': user.name,
                'email': user.email,
                'session_id': request.session.sid  # Return session ID
            }

        except Exception as e:
            return {'status': 'error', 'message': str(e)}
