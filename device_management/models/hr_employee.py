import os
import base64
import qrcode
from io import BytesIO
from odoo import models, fields, api, _
from odoo.tools import config

from odoo.exceptions import ValidationError


class Employee(models.Model):
    _inherit = "hr.employee"

    qr_code = fields.Binary(string='QR Code', compute='_compute_qr_code', store=True)
    is_hr_desk = fields.Boolean(string='Is HR Desk', default=False, tracking=True)
    active = fields.Boolean(default=True)

    @api.depends('emp_code')
    def _compute_qr_code(self):
        """Generate QR Code for Employee and store it as a binary field."""
        print("------------------called-------------------")
        for record in self:
            if record.emp_code:
                print("---------if------self.emp_code", record.emp_code)
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=5,
                )
                qr.add_data(record.emp_code)
                qr.make(fit=True)

                # Convert QR code image to binary (PNG format)
                img = qr.make_image(fill='black', back_color='white')
                img_bytes = BytesIO()
                img.save(img_bytes, format='PNG')

                # Encode image as base64 and assign to qr_code field
                record.qr_code = base64.b64encode(img_bytes.getvalue())

            # else:
            #     raise ValidationError(_("Employee code is required"))

            print("---------------self.qr_code", self.qr_code)

    def generate_qr_code_employee(self):
        self._compute_qr_code()

    # def get_qr_code(self):
    #     """Generate QR Code for Employee and return the web path."""
    #     if self.barcode:
    #         print("---------if------self.barcode", self.barcode)
    #         qr_dir = os.path.join(config['data_dir'], 'qrcode')
    #         print("---------------qr_dir", qr_dir)
    #         if not os.path.exists(qr_dir):
    #             os.makedirs(qr_dir)
    #         print("---------------os.path.exists(qr_dir)", os.path.exists(qr_dir))
    #
    #         qr_path = os.path.join(qr_dir, f"{self.barcode}.png")
    #         print("---------------qr_path", qr_path)
    #         if os.path.exists(qr_path):
    #             with open(qr_path, "rb") as f:
    #                 self.qr_code = f.read()
    #         if not os.path.exists(qr_path):
    #             qr = qrcode.QRCode(
    #                 version=1,
    #                 error_correction=qrcode.constants.ERROR_CORRECT_L,
    #                 box_size=10,
    #                 border=5,
    #             )
    #             print("---------------qr", qr)
    #             qr.add_data(self.barcode)
    #             qr.make(fit=True)
    #             self.qr_code = qr.make_image(fill='black', back_color='white').tobytes()
    #             img = qr.make_image(fill='black', back_color='white')
    #             print("---------------img", img)
    #             img.save(qr_path)
    #     else:
    #         print("---------else------self.barcode", self.barcode)
    #         self.generate_random_barcode()
    #         self.get_qr_code()