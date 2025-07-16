from odoo import models, fields, api
import uuid
from urllib.parse import urljoin


class SignatureRequest(models.Model):
    _name = 'signature.request'
    _description = 'Document Signature Request'

    name = fields.Char(default=lambda self: str(uuid.uuid4()), readonly=True)
    employee_id = fields.Many2one('hr.employee', required=True)
    contract_id = fields.Many2one('hr.contract', required=True)
    token = fields.Char(string="Token", default=lambda self: str(uuid.uuid4()), readonly=True)
    document_attachment_id = fields.Many2one('ir.attachment', string="Document")
    signed_document_id = fields.Many2one('ir.attachment', string="Signed Document")
    is_signed = fields.Boolean(default=False)
    signature_image = fields.Binary("Signature Image")


    def get_portal_url(self):
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        # Optional: generate and store a token if required
        # Example token: uuid.uuid4().hex or stored in a separate field
        print("\nDebug----------------------base_url", base_url)
        return urljoin(base_url, f"/sign-document/{self.token}")