from odoo import http
from odoo.http import request
import base64, io, fitz


class DocumentSignController(http.Controller):

    @http.route(['/sign-document/<string:token>'], type='http', auth="public", website=True, methods=['GET','POST'])
    def sign_document(self, token, **kw):
        print("\nDebug----------------------token", token)
        request_obj = request.env['signature.request'].sudo().search([('token', '=', token), ('is_signed', '=', False)], limit=1)
        print("\nDebug----------------------request_obj", request_obj)
        print("\nDebug----------------------request_obj.employee_id", request_obj.employee_id)
        if not request_obj:
            return request.render("custom_employee.signature_invalid_token")

        # Get all related documents for this contract

        return request.render("custom_employee.realtime_signing_form", {
            'object': request_obj,
            'pdf_url': "/web/content/%s?download=false" % request_obj.document_attachment_id.id,
        })

        # related_requests = request.env['signature.request'].sudo().search([
        #     ('contract_id', '=', request_obj.contract_id.id),
        #     ('is_signed', '=', False)
        # ])
        # print("\nDebug----------------------related_requests", related_requests)
        #
        # return request.render("custom_employee.signature_form", {
        #     'object': request_obj,
        #     'related_requests': related_requests
        # })

    @http.route(['/submit-signature'], type='http', auth="public", methods=['POST'], csrf=False)
    def submit_signature(self, **post):
        token = post.get('token')
        signature_data = post.get('signature_data')

        request_obj = request.env['signature.request'].sudo().search([
            ('token', '=', token), ('is_signed', '=', False)
        ], limit=1)

        if not request_obj:
            return "Invalid Request"

        signature_image = base64.b64decode(signature_data.split(',')[1])
        pdf_data = request_obj.document_attachment_id.raw

        doc = fitz.open(stream=pdf_data, filetype="pdf")
        page = doc[-1]  # Last page

        # Insert signature image
        img_rect = fitz.Rect(400, 50, 550, 150)
        page.insert_image(img_rect, stream=signature_image)

        # Insert signer info + timestamp
        signer = request_obj.employee_id.name
        signed_on = request_obj.create_date.strftime("%Y-%m-%d %H:%M")
        page.insert_text((50, 760), f"Signed by {signer} on {signed_on}", fontsize=10, color=(0, 0, 0))

        output = io.BytesIO()
        doc.save(output)
        doc.close()

        signed_attachment = request.env['ir.attachment'].sudo().create({
            'name': f'Signed Document - {request_obj.contract_id.name}.pdf',
            'type': 'binary',
            'datas': base64.b64encode(output.getvalue()),
            'res_model': 'hr.contract',
            'res_id': request_obj.contract_id.id,
        })

        request_obj.write({
            'is_signed': True,
            'signed_document_id': signed_attachment.id,
            'signature_image': base64.b64encode(signature_image)
        })

        return request.render("custom_employee.signature_success")

    # @http.route(['/submit-signature'], type='http', auth="public", methods=['POST'], csrf=False)
    # def submit_signature(self, **post):
    #     token = post.get('token')
    #     signature_data = post.get('signature_data')
    #
    #     print("\nDebug----------------------token", token)
    #     print("\nDebug----------------------signature_data", signature_data)
    #
    #     request_obj = request.env['signature.request'].sudo().search([('token', '=', token)], limit=1)
    #     if not request_obj:
    #         return "Invalid Request"
    #
    #     if signature_data:
    #         signature_image = base64.b64decode(signature_data.split(',')[1])
    #
    #         # Load original PDF
    #         pdf_data = request_obj.document_attachment_id.raw
    #         doc = fitz.open(stream=pdf_data, filetype="pdf")
    #         page = doc[0]
    #
    #         # Insert signature image at bottom right
    #         img_rect = fitz.Rect(400, 50, 550, 150)
    #         page.insert_image(img_rect, stream=signature_image)
    #
    #         # Save signed PDF
    #         signed_stream = io.BytesIO()
    #         doc.save(signed_stream)
    #         signed_pdf_data = signed_stream.getvalue()
    #         doc.close()
    #
    #         signed_attachment = request.env['ir.attachment'].sudo().create({
    #             'name': 'Signed Document - %s.pdf' % request_obj.contract_id.name,
    #             'type': 'binary',
    #             'datas': base64.b64encode(signed_pdf_data),
    #             'res_model': 'hr.contract',
    #             'res_id': request_obj.contract_id.id,
    #         })
    #
    #         request_obj.write({
    #             'is_signed': True,
    #             'signed_document_id': signed_attachment.id,
    #             'signature_image': base64.b64encode(signature_image)
    #         })
    #
    #         print("\nDebug----------------------signed_attachment", signed_attachment)
    #         print("\nDebug----------------------request_obj", request_obj)
    #
    #     return request.render("custom_employee.signature_success")