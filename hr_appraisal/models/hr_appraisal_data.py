# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError
from pygments.lexer import default


class HrAppraisalData(models.Model):
    _name = 'hr.appraisal.data'
    _description = 'Appraisal Data'
    _rec_name = 'name'

    name = fields.Char(string="Name")
    appraisal_id = fields.Many2one('hr.appraisal', string="Appraisal")
    last_goals_ids = fields.One2many('last.evaluation.goal', 'appraisal_data_id', string="Last Goals")
    future_goals_ids = fields.One2many('future.evaluation.goal', 'appraisal_data_id', string="Future Goals")
    attribute_data_ids = fields.One2many('attribute.data', 'appraisal_data_id', string="Ratings")
    additional_point = fields.Text(string="Additional Points")
    portal_filled = fields.Boolean(string="Portal Filled")
    goals_notes_ids = fields.One2many('goals.notes.evalutor', 'appraisal_data_id', string="Last Goals")
    comment = fields.Text(string="Evaluator Comments")


class LastEvaluationGoal(models.Model):
    _name = 'last.evaluation.goal'
    _description = 'Last Evaluation Goals'

    name = fields.Char(string="Name")
    action_taken = fields.Char(string="Action Taken")
    is_completed = fields.Boolean(string="Is Completed?")
    appraisal_data_id = fields.Many2one('hr.appraisal.data', string="Appraisal Data")
    portal_filled = fields.Boolean(string="Portal Filled")


class FutureEvaluationGoals(models.Model):
    _name = 'future.evaluation.goal'
    _description = 'Future Evaluation Goals'

    name = fields.Char(string="Name")
    action_needs = fields.Char(string="Action Needs to be Taken")
    estimation_time = fields.Char(string="Estimated Time")
    appraisal_data_id = fields.Many2one('hr.appraisal.data', string="Appraisal Data")
    portal_filled = fields.Boolean(string="Portal Filled")


class Attributes(models.Model):
    _name = 'attribute.attribute'
    _description = 'Attributes Data'

    name = fields.Char(string="Name")
    active = fields.Boolean(string="Active", default=True)


class AttributesData(models.Model):
    _name = 'attribute.data'
    _description = 'Attribute Data'

    attribute_id = fields.Many2one('attribute.attribute', string="Attribute")
    average_rating = fields.Integer(string="Average Rating", compute="_compute_average_rating", store=True)
    appraisal_data_id = fields.Many2one('hr.appraisal.data', string="Appraisal Data")
    attribute_manager_ids = fields.One2many('attribute.manager.rating', 'attribute_data_id', string="Managers")

    @api.depends('attribute_manager_ids.rating')
    def _compute_average_rating(self):
        for record in self:
            ratings = record.attribute_manager_ids.mapped('rating')
            print("\nDebug------------------ratings", ratings)
            employee = record.attribute_manager_ids.mapped('employee_id')
            print("\nDebug------------------employee", employee)

            if ratings:
                record.average_rating = sum(ratings) / len(ratings)
            else:
                record.average_rating = 0.0


class AttributeManagerRating(models.Model):
    _name = 'attribute.manager.rating'
    _description = 'Attribute Manager Ratings'
    _rec_name = 'employee_id'

    attribute_data_id = fields.Many2one('attribute.data', string="Attribute Data")
    attribute_id = fields.Many2one('attribute.attribute', related='attribute_data_id.attribute_id', string="Attribute")
    employee_id = fields.Many2one('hr.employee', string="Manager")
    rating = fields.Integer(string="Rating")
    notes = fields.Char(string="Notes")


class GoalsNotesEvalutor(models.Model):
    _name = 'goals.notes.evalutor'
    _description = 'Goals Notes Evalutor'

    name = fields.Char(string="Goal")
    note = fields.Char(string="Note")
    appraisal_data_id = fields.Many2one('hr.appraisal.data', string="Appraisal Data")
