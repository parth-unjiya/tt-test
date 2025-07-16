from odoo import models, fields, api

class UserQRCode(models.Model):
    _name = 'user.qr.code'
    _description = 'User QR Code'
    _inherit = ['mail.thread']

    user_id = fields.Many2one('res.users', string='User', required=True, tracking=True)
    qr_code = fields.Binary(string='QR Code', attachment=True)
    is_hr_desk = fields.Boolean(string='Is HR Desk', default=False, tracking=True)
    active = fields.Boolean(default=True)

    @api.model_create_multi
    def create(self, vals):
        record = super(UserQRCode, self).create(vals)
        record._generate_qr_code()
        return record

    def _generate_qr_code(self):
        import qrcode
        import base64
        from io import BytesIO
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        data = f'hr_desk' if self.is_hr_desk else f'user_{self.user_id.id}'
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color='black', back_color='white')
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        self.qr_code = base64.b64encode(buffered.getvalue()) 