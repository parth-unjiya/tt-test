# -*- coding: utf-8 -*-

from odoo import fields, models


class QuestionSelection(models.Model):
    """Model to store options for selection type question"""
    _name = 'question.selection'
    _description = 'Selection Question'

    name = fields.Char(string='Name', help="Selection value.")
    question_id = fields.Many2one('survey.question',
                                  string="Question",
                                  help="Field to store "
                                       "question id in selection type.")
