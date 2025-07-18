# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SurveyQuestion(models.Model):
    """ Inherited survey.question to add custom question type"""
    _inherit = 'survey.question'


    tt_id = fields.Char(string="TT ID")
    selection_ids = fields.One2many('question.selection',
                                    'question_id',
                                    string='Select',
                                    help="""Field used to create selection type
                                     questions""")
    question_type = fields.Selection(selection_add=[
        ('time', 'Time'),
        ('month', 'Month'),
        ('name', 'Name'),
        ('address', 'Address'),
        ('email', 'Email'),
        ('password', 'Password'),
        ('qr', 'Qrcode'),
        ('url', 'URL'),
        ('week', 'Week'),
        ('color', 'Color'),
        ('range', 'Range'),
        ('many2one', 'Many2one'),
        ('file', 'Upload File'),
        ('many2many', 'Many2many'),
        ('selection', 'Selection'),
        ('barcode', 'Barcode')
    ], help="Survey supported question types")
    matrix_subtype = fields.Selection(
        selection_add=[('custom', 'Custom Matrix')],
        help="""Matrix selection type question""")
    model_id = fields.Many2one('ir.model', string='Model',
                               domain=[('transient', '=', False)],
                               help="Many2one type question")
    range_min = fields.Integer(string='Min',
                               help='Minimum range,range type question')
    range_max = fields.Integer(string='Max',
                               help='Maximum range,range type question')
    qrcode = fields.Text(string='Qrcode',
                         help='Show qrcode in survey')
    qrcode_png = fields.Binary(string='Qrcode PNG', help="Qrcode PNG")
    barcode = fields.Char(string='Barcode', help="Barcode number")
    barcode_png = fields.Binary(string='Barcode PNG',
                                help="Saves barcode png file")

    @api.onchange('barcode')
    def _onchange_barcode(self):
        """Onchange function to restrict barcode less-than 12 character """
        if self.barcode:
            if len(self.barcode) < 12:
                raise ValidationError(
                    _("Make sure barcode is at least 12 letters"))
            if len(self.barcode) > 12:
                raise ValidationError(
                    _("There should not be more than 12 "
                      "characters in a barcode"))
            if not self.barcode.isdigit():
                raise ValidationError(_("Only digits are allowed."))

    def get_selection_values(self):
        """Function return options for selection type question"""
        return self.selection_ids

    def prepare_model_id(self, model):
        """Function to return options for many2one question"""
        if model:
            model_data = self.env[model.model].sudo().search([])
            return [rec.read([model_data._rec_name])[0] for rec in model_data]
        model_data = self.env[self.model_id.model].sudo().search([])
        return [rec.read([model_data._rec_name])[0] for rec in model_data]
