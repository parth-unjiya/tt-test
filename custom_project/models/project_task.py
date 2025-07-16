from odoo import api, fields, models
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class ProjectTask(models.Model):
    _inherit = "project.task"

    task_update_from_tt = fields.Char(string="Task Update from TT")
    type = fields.Char(string="Type", default="W")
    module_id = fields.Many2one(comodel_name="project.module", string="Module")
    is_running_tt = fields.Boolean(string="Is Running TT", default=False)
    is_meeting_task = fields.Boolean(string="Is Meeting", default=False)
    task_type = fields.Selection([("task", "Task"), ("issue", "Bug")], default="task")
    priority = fields.Selection(
        selection_add=[
            ('1', 'Normal'),
            ('2', 'High'),
        ],
    )
    reproducibility = fields.Selection([
            ('always', 'Always'),
            ('sometimes', 'Sometimes'),
            ('random', 'Random'),
            ('not_tried', 'Have Not Tried'),
            ('unable_to_reproduce', 'Unable to Reproduce'),
            ('na', 'N/A'),
        ], string='Reproducibility'
    )
    severity = fields.Selection([
        ('feature', 'Feature'),
        ('trivial', 'Trivial'),
        ('text', 'Text'),
        ('minor', 'Minor'),
        ('major', 'Major'),
        ('crash', 'Crash'),
        ('block', 'Block'),
    ], string='Severity')

    summary = fields.Text(string='Summary')
    steps_to_reproduce = fields.Html(string='Steps to Reproduce')
    additional_info = fields.Text(string='Additional Info')
    issue_category_id = fields.Many2one(
        'issue.category', 
        string='Issue Category',
        help='Category of the issue or bug'
    )

    def action_issue(self):
        self.ensure_one()
        return {
            "name": "Convert to Issue",
            "type": "ir.actions.act_window",
            "res_model": "project.task",
            "view_mode": "form",
            "target": "new",  # opens in a modal
            "context": {
                "default_task_type": "issue",
                "default_parent_id": self.id,
                "default_project_id": self.project_id.id,
                "default_user_ids": self.user_ids.ids,
                "default_milestone_id": self.milestone_id.id,
                "default_allocated_hours": self.allocated_hours,
                "default_start_date": self.start_date,
                "default_date_deadline": self.date_deadline,
            },
        }



class IssueCategory(models.Model):
    _name = 'issue.category'
    _description = 'Issue Category'

    name = fields.Char(string='Name', required=True)