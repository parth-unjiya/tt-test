# -*- coding: utf-8 -*-
import uuid
import base64
import logging

from datetime import timedelta
from markupsafe import Markup

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)



class ProjectAcceptanceReport(models.Model):
    _name = "project.acceptance.report"
    _description = "Project Acceptance Report"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    # Project & Client Info
    project_id = fields.Many2one("project.project", string="Project", required=True)
    client_id = fields.Many2one(
        "res.partner", string="Client", related="project_id.partner_id", store=True
    )
    project_manager_id = fields.Many2one(
        "res.users", string="Project Manager", related="project_id.user_id", store=True
    )

    # Agreement & Dates
    agreement_files = fields.Many2many(
        "ir.attachment", string="Agreement / WBS References",
        domain="[('res_model', '=', 'project.project'), ('res_id', '=', project_id)]"
    )
    date_of_execution = fields.Date(string="Date of Execution of the Agreement")
    date_of_completion = fields.Date(string="Date of Project Completion")

    # Project Scope Info
    note = fields.Text(string="Note")
    project_aliases = fields.Char(string="Project Aliases", related="project_id.name")

    milestone_ids = fields.Many2many("project.milestone", string="Milestone Name")
    deliverable_line_ids = fields.One2many('project.acceptance.deliverable', 'report_id', string="Deliverables")


    # PM Signature
    pm_signature = fields.Binary(string="PM Signature", attachment=True)
    pm_signed_by = fields.Char(string="PM Signed By")
    pm_signed_on = fields.Date(string="PM Signed On")

    # Client Signature
    client_signature = fields.Binary(string="Client Signature", attachment=True)
    client_signed_by = fields.Char(string="Client Signed By")
    client_signed_on = fields.Date(string="Client Signed On")

    # Other
    annexure_link = fields.Char(string="Annexure Link")

    stage = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('accept', 'Accepted'),
        ('reject', 'Rejected'),
    ], string="Stage", default="draft", tracking=True)

    token = fields.Char('Access Token', index=True)
    token_expiry = fields.Datetime('Token Expiry')

    def action_send_to_client(self):
        self.ensure_one()

        template = self.env.ref('custom_project.project_acceptance_portal_email_template', raise_if_not_found=False)
        if not template:
            raise UserError(_("Email template not found."))

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', default='')

        now = fields.Datetime.now()
        if not self.token or not self.token_expiry or now > self.token_expiry:
            self.token = str(uuid.uuid4())
            self.token_expiry = now + timedelta(days=4)

        portal_url = f"{base_url}/project/acceptance/{self.id}?access_token={self.token}"

        ctx = {
            'portal_url': portal_url,
            'token_expiry': self.token_expiry,
        }

        template.with_context(ctx).send_mail(self.id, force_send=True)

        self.project_id.message_post(
            body=Markup(_("Acceptance report has been sent to <strong>%s</strong>") %
                 (self.client_id.name)),
            message_type="comment",
        )

        self.stage = 'sent'

    def action_print_pdf(self):
        return self.env.ref("custom_project.action_project_acceptance_report_pdf").report_action(self)

    def action_preview_report(self):
        """Preview the milestone report in HTML (web preview)."""
        self.ensure_one()
        return self.env.ref("custom_project.action_project_acceptance_report_html").report_action(self, config=False)

    def unlink(self):
        for rec in self:
            if rec.stage != 'draft':
                raise UserError(_("You can only delete milestones in 'Draft' stage."))
        return super().unlink()

    def action_draft(self):
        self.stage = "draft"

    def action_accept(self):
        self.ensure_one()
        self._send_acceptance_email()

    def action_reject(self):
        self.ensure_one()
        self._send_acceptance_email(rejected=True)

    def _send_acceptance_email(self, auto_accepted=False, rejected=False):
        pdf_content = self.env['ir.actions.report']._render_qweb_pdf(
            "custom_project.action_project_acceptance_report_pdf", self.id
        )
        filename = f"Project_Acceptance_{self.project_id.name or 'report'}.pdf"

        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(pdf_content[0]),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })

        template = self.env.ref("custom_project.project_acceptance_client_email_template")

        # CC operation managers and project manager
        group = self.env.ref('custom_dashboard.group_dashboard_operation_manager')
        users = self.env['res.users'].search([('groups_id', 'in', [group.id]), ('email', '!=', False)])
        cc_emails = set(user.email for user in users)
        
        if self.project_id.user_id.email:
            cc_emails.add(self.project_id.user_id.email)

        ctx = {
            'auto_accepted': auto_accepted,
            'rejected': rejected,
            'email_cc': ', '.join(cc_emails),
        }

        template.attachment_ids = [(4, attachment.id)]
        template.with_context(ctx).send_mail(self.id, force_send=True)
        template.attachment_ids = [(5, 0, 0)]


    @api.model
    def _cron_auto_accept_project_reports(self):
        now = fields.Datetime.now()
        records = self.search([
            ('stage', '=', 'sent'),
            ('token_expiry', '<', now)
        ])
        for rec in records:
            _logger.info(f"Auto-accepting project acceptance report ID {rec.id}")
            rec.stage = 'accept'
            rec._send_acceptance_email(auto_accepted=True)



class ProjectAcceptanceDeliverable(models.Model):
    _name = 'project.acceptance.deliverable'
    _description = 'Acceptance Report Deliverable Line'

    report_id = fields.Many2one('project.acceptance.report', string="Report", ondelete="cascade")
    deliverable = fields.Char(string="Deliverable Name")
    repository_link = fields.Char(string="Repository / Client Link")
    notes = fields.Html(string="Notes")