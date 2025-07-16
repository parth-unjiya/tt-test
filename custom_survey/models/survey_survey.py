# -*- coding: utf-8 -*-

from odoo import fields, models


class Survey(models.Model):
    """Inherited model to change survey visibility"""
    _inherit = 'survey.survey'

    tt_id = fields.Char(string="TT ID")
    is_candidate_form_create = fields.Boolean(string="Is Candidate Form Create", default=False)
    is_appraisal_form = fields.Boolean(string="Is Appraisal Form Create", default=False)
    access_mode = fields.Selection(selection_add=[
        ('website', 'website')], ondelete={'website': 'cascade'})
    visibility = fields.Boolean(string='Portal Visibility',
                                help="""Portal visibility of this survey""")

    def action_answer_report_download(self):
        """Function to generate report values"""
        return {
            'type': 'ir.actions.act_url',
            'url': f'/xlsx_report/{self.id}'
        }
