
from odoo import api, fields, models


class SurveyUserInput(models.Model):
    """Inherits the model survey.user_input to extend the model and make
    changes in the functionality."""
    _inherit = 'survey.user_input'

    interview_review_id = fields.Many2one('hr.applicant', string="Interview review id")

    @api.model_create_multi
    def create(self, vals):
        """inherits the create method of the model survey.user_input"""
        ctx = self.env.context
        if ctx.get('active_id') and ctx.get('active_model') == 'hr.applicant':
            vals[0]['interview_review_id'] = ctx.get('active_id')
        return super(SurveyUserInput, self).create(vals)