import logging

from datetime import timedelta
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class Project(models.Model):
    _inherit = 'project.project'

    release_note_ids = fields.One2many('release.note', 'project_id', string="Release Notes")
    milestone_acceptance_ids = fields.One2many('milestone.completion.report', 'project_id', string="Milestone Acceptance")
    design_hours = fields.Float(string="Design Hours")
    development_hours = fields.Float(string="Development Hours")
    qc_hours = fields.Float(string="QC Hours")
    management_hours = fields.Float(string="Management Hours")
    other_hours = fields.Float(string="Other Hours")
    user_has_group_admin = fields.Boolean(string="Admin", compute="compute_user_groups")

    def compute_user_groups(self):
        for rec in self:
            rec.user_has_group_admin = self.env.user.has_group('project.group_project_manager') or self.env.user.has_group(
                'sales_team.group_sale_salesman')

    project_acceptance_report_ids = fields.One2many('project.acceptance.report', 'project_id', string="Project Acceptance")

    @api.depends('design_hours', 'development_hours', 'qc_hours', 'management_hours', 'other_hours')
    def _compute_total_allocated_hours(self):
        for record in self:
            record.allocated_hours = (
                    record.design_hours +
                    record.development_hours +
                    record.qc_hours +
                    record.management_hours +
                    record.other_hours
            )

    allocated_hours = fields.Float(
        string='Allocated Hours',
        compute='_compute_total_allocated_hours',
        store=True
    )

    @api.model_create_multi
    def create(self, vals):
        project = super(Project, self).create(vals)

        # Define default stage names and order
        default_stages = [
            ('Pending', 1),
            ('In Development', 2),
            ('In QA', 3),
            ('In Staging', 4),
            ('Completed', 5),
            ('Canceled', 6),
        ]

        stage_ids = []

        for name, seq in default_stages:
            stage = self.env['project.task.type'].search([('name', '=', name)], limit=1)
            if not stage:
                stage = self.env['project.task.type'].create({
                    'name': name,
                    'sequence': seq,
                    'fold': name == 'Canceled',
                })
            stage_ids.append(stage.id)

        project.write({'type_ids': [(6, 0, stage_ids)], 'privacy_visibility': 'followers'})
        
        # Trigger only if project is linked to sale order
        if project.sale_order_id:
            _logger.info(f"Creating project {project.name} for sale order {project.sale_order_id.name}...")
            project.send_creation_notification()

        return project

    @api.onchange('stage_id')
    def send_survey_form_to_project_manager(self):
        if self.stage_id.name == 'Done':
            project_manager = self.user_id
            project_user_ids = self.task_ids.mapped('user_ids')

            base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
            survey_obj = self.env["survey.survey"]
            
            # Retrieve the survey
            survey_title = 'SOP Project Review'
            manager_survey = survey_obj.search([
                ('active', '=', True), 
                ('title', '=', survey_title),
            ], limit=1)
            
            if not manager_survey:
                _logger.warning(f"Survey '{survey_title}' not found.")
                return

            for emp in project_user_ids:
                # Skip the project manager
                if emp.id == project_manager.id:
                    continue
                
                if not emp.email:
                    _logger.warning(f"No email found for employee {emp.name} (ID: {emp.id}). Skipping.")
                    continue

                # Create survey response
                response = manager_survey._create_answer(
                    survey_id=manager_survey.id,
                    deadline=fields.Date.today() + timedelta(days=5),
                    partner=project_manager,
                    email=emp.email,
                )

                if not response:
                    _logger.error(f"Failed to create survey response for employee {emp.name}.")
                    continue

                # Construct the URL and email content
                survey_url = response.get_start_url()
                mail_content = f"""
                    Dear {project_manager.name},
                    <br/><br/>
                    Please fill out the following review form related to {emp.name}'s 
                    <br/>
                    Project Name: {self.name}.
                    <br/><br/>
                    <a href="{base_url}{survey_url}">Click here to access the project review form</a>
                    <br/><br/>
                    Please submit your response by: {response.deadline}
                """

                # Prepare email values
                mail_values = {
                    "model": "hr.employee.probation.review",
                    "res_id": self.ids[0],
                    "subject": f"Project Review for {emp.name}",
                    "recipient_ids": [(6, 0, [emp._origin.id])],  # Ensure recipient is linked properly
                    "body_html": mail_content,
                    "email_from": self.env.user.email or None,
                    "auto_delete": False,
                    "email_to": project_manager.email,
                }

                # Send the email
                mail = self.env["mail.mail"].sudo().create(mail_values)
                mail._send()

                _logger.info(f"Survey email sent to {emp.email} for employee {emp.name}.")


    def send_creation_notification(self):
        odoobot = self.env['res.partner'].sudo().search([
            ('name', '=', 'OdooBot'), ('active', '=', False)
        ], limit=1)

        if not odoobot:
            _logger.warning("OdooBot not found.")
            return

        group = self.env.ref('custom_dashboard.group_dashboard_operation_manager')  # use your group XML ID
        users = self.env['res.users'].sudo().search([('groups_id', 'in', [group.id])])

        for user in users:
            self.message_notify(
                partner_ids=[user.partner_id.id],
                subject='New Project Created',
                body=f'Project {self.name} has been created from a Sale Order: {self.sale_order_id.name}',
                model=self._name,
                res_id=self.id,
                author_id=odoobot.id,
                record_name=self.name,
            )

    def get_panel_data(self):
        # If user is NOT project manager
        if not self.user_has_groups('project.group_project_manager'):
            show_profitability = self._show_profitability()

            panel_data = {
                'user': self._get_user_values(),
                'buttons': sorted(self._get_stat_buttons(), key=lambda k: k['sequence']),
                'currency_id': self.currency_id.id,
                'show_project_profitability_helper': show_profitability and self._show_profitability_helper(),
            }

            if self.allow_milestones:
                panel_data['milestones'] = self._get_milestones()

            if show_profitability:
                profitability_items = self._get_profitability_items()

                # If user can't see it, pass empty
                panel_data.update({
                    'profitability_items': {
                        'costs': {'data': [], 'total': {'billed': 0.0, 'to_bill': 0.0}},
                        'revenues': {'data': [], 'total': {'invoiced': 0.0, 'to_invoice': 0.0}},
                    },
                    'profitability_labels': {},
                })

            return panel_data

        # Default for project managers
        return super().get_panel_data()


