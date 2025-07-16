
from odoo import api, fields, models


class SurveyUserInput(models.Model):
    """Inherits the model survey.user_input to extend the model and make
    changes in the functionality."""
    _inherit = 'survey.user_input'

    review_id = fields.Many2one('hr.employee.probation.review', string="Review id")

    @api.model_create_multi
    def create(self, vals):
        """inherits the create method of the model survey.user_input"""
        ctx = self.env.context
        print(">>>>>>----ctx",ctx)
        if ctx.get('params'):
            if ctx.get('params').get('id') and ctx.get('params').get('model') == 'hr.employee':
                employee_id = self.env['hr.employee'].browse(ctx.get('params').get('id'))
                review_ids = employee_id.review_ids
                for rec in review_ids:
                    if rec.review_status != 'done':
                        print(rec)
                        vals['review_id'] = rec.id
        else:
            if ctx.get('review_id'):
                vals['review_id'] = ctx.get('review_id').id
            print(self.review_id)
        return super(SurveyUserInput, self).create(vals)
    

class CustomSurvey(models.Model):
    _inherit = 'survey.survey'

    is_review_form = fields.Boolean(string="Is a probation review form")
