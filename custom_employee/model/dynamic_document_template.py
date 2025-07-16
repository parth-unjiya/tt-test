from odoo import models, fields, api


class DocumentTemplate(models.Model):
    _name = 'document.template'
    _description = 'Dynamic Document Template'


    @api.model
    def default_get(self, fields):
        res = super(DocumentTemplate, self).default_get(fields)
        if res.get('model'):
            res['model_id'] = self.env['ir.model']._get(res.pop('model')).id
        return res

    name = fields.Char("Template Name", required=True)
    model_id = fields.Many2one('ir.model', 'Applies to')
    model = fields.Char('Related Document Model', related='model_id.model', index=True, store=True, readonly=True)
    body_html = fields.Html(
        'Document Body (HTML)',
        prefetch=True, translate=True, sanitize=False)

    description = fields.Text("Description")
