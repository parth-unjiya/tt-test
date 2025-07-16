from odoo import models, fields, api
import base64
from odoo.exceptions import UserError
import pdfkit


class ContractDocumentWizard(models.TransientModel):
    _name = 'contract.document.wizard'
    _description = 'Contract Document Wizard'

    contract_id = fields.Many2one('hr.contract', string='Contract', required=True, readonly=True)
    document_template_ids = fields.Many2many('document.template', string='Select Templates')

    def action_generate_documents(self):
        if not self.document_template_ids:
            raise UserError("Please select at least one document template.")

        for template in self.document_template_ids:
            # Render template (you can use jinja or QWeb if needed)
            html_content = template.body_html
            # pdf_bytes = self.env.ref('web.html_to_pdf')._render_html_to_pdf(html_content)[0]
            pdf_bytes = pdfkit.from_string(html_content, False)

            attachment = self.env['ir.attachment'].create({
                'name': template.name + ".pdf",
                'type': 'binary',
                'datas': base64.b64encode(pdf_bytes),
                'res_model': 'hr.contract',
                'res_id': self.contract_id.id,
                'public': True
            })

            signature_request = self.env['signature.request'].create({
                'employee_id': self.contract_id.employee_id.id,
                'contract_id': self.contract_id.id,
                'document_attachment_id': attachment.id,
            })

            template = self.env.ref('custom_employee.signature_email_template')

            if template:
                template.sudo().with_context(
                    signature_link=f"/sign-document/{signature_request.token}",
                    employee_name=self.contract_id.employee_id.name,
                    document_name=template.name,
                ).send_mail(signature_request.id, force_send=True)

        return {'type': 'ir.actions.act_window_close'}
