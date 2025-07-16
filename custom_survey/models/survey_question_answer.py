# -*- coding: utf-8 -*-

from odoo import fields, models


class SurveyQuestionAnswer(models.Model):
    """Inherit question answer model to add new answer type and model field"""
    _inherit = 'survey.question.answer'

    answer_type = fields.Selection([
        ('text_box', 'Multiple Lines Text Box'),
        ('char_box', 'Single Line Text Box'),
        ('numerical_box', 'Numerical Value'),
        ('time', 'Time'),
        ('email', 'Email'),
        ('password', 'Password'),
        ('range', 'Range'),
        ('month', 'Month'),
        ('url', 'URL'),
        ('week', 'Week'),
        ('color', 'Color'),
        ('many2one', 'Many2one')], help="Answer type",
        string='Answer Type', readonly=False, store=True)
    model_id = fields.Many2one('ir.model', string='Model',
                               domain=[('transient', '=', False)],
                               help="Select model for getting it's"
                                    " values in survey")
