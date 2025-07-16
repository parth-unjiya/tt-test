# -*- coding: utf-8 -*-
import uuid
import base64
import logging

from markupsafe import Markup, escape
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MilestoneCompletionReport(models.Model):
    _name = "milestone.completion.report"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Milestone Completion Report"

    project_id = fields.Many2one("project.project", string="Project", readonly=True)
    milestone_ids = fields.Many2many("project.milestone", string="Milestones")
    partner_id = fields.Many2one(
        "res.partner",
        related="project_id.partner_id",
        string="Partner",
        store=True,
        readonly=True,
    )
    manager_id = fields.Many2one(
        "res.users",
        related="project_id.user_id",
        string="Manager",
        store=True,
        readonly=True,
    )
    reached_date = fields.Date(string="Reached Date")
    client_comment = fields.Text(string="Client Comment")
    deliverables = fields.Html(string="Deliverables")
    date_of_execution_agreement = fields.Date(string="Date of Execution Agreement")
    annexure_link = fields.Char(string="Annexure Link")
    
    token = fields.Char("Access Token", index=True)
    token_expiry = fields.Datetime("Token Expiry")

    signed_by = fields.Char(readonly=True)
    signed_on = fields.Datetime(readonly=True)
    signature = fields.Binary(attachment=True, copy=False)

    stage = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('accept', 'Accepted'),
        ('reject', 'Rejected'),
    ], string="Stage", default="draft", tracking=True)

    @api.onchange("milestone_ids")
    def _onchange_milestone_ids(self):
        """Auto-populate deliverables based on selected milestones and their tasks."""
        if self.milestone_ids:
            blocks = []
            for milestone in self.milestone_ids:
                task_lines = []
                for task in milestone.task_ids:
                    task_lines.append(f"<li>{escape(task.name)}</li>")
                if task_lines:
                    block = f"<p><strong>{escape(milestone.name)}</strong></p><ul>{''.join(task_lines)}</ul>"
                else:
                    block = f"<p><strong>{escape(milestone.name)}</strong></p><p><em>No tasks available</em></p>"
                blocks.append(block)
            self.deliverables = "".join(blocks)
        else:
            self.deliverables = False

    def action_print_pdf(self):
        """Trigger PDF report for this milestone."""
        self.ensure_one()
        return self.env.ref("custom_project.action_milestone_report_pdf").report_action(self)

    def action_preview_report(self):
        """Preview the milestone report in HTML (web preview)."""
        self.ensure_one()
        return self.env.ref("custom_project.action_milestone_report_html").report_action(self, config=False)

    def action_send_to_customer(self):
        """Generate token, construct portal URL, send milestone email, and log it."""
        self.ensure_one()

        template = self.env.ref(
            'custom_project.milestone_completion_portal_email_template',
            raise_if_not_found=False
        )
        if not template:
            raise UserError(_(
                "Email template not found: 'custom_project.milestone_completion_portal_email_template'"
            ))

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', default='')

        now = fields.Datetime.now()
        if not self.token or not self.token_expiry or now > self.token_expiry:
            self.token = str(uuid.uuid4())
            self.token_expiry = now + timedelta(days=4)

        portal_url = f"{base_url}/milestone/{self.id}?access_token={self.token}"

        ctx = {
            'portal_url': portal_url,
            'token_expiry': self.token_expiry,
        }

        template.with_context(ctx).send_mail(self.id, force_send=True)

        msg = _(
            "Milestone review email has been sent to %(name)s .",
            name=Markup("<strong>%s</strong>" % self.partner_id.name),
        )

        self.project_id.message_post(
            body=msg,
            message_type="comment",
            subtype_xmlid="mail.mt_note",
        )

        self.stage = "sent"

    def unlink(self):
        for rec in self:
            if rec.stage != 'draft':
                raise UserError(_("You can only delete milestones in 'Draft' stage."))
        return super().unlink()

    def action_draft(self):
        self.stage = "draft"

    def action_accept(self):
        self.ensure_one()
        self.send_client_acceptance_email()

    def action_reject(self):
        self.ensure_one()
        self.send_client_acceptance_email(rejected=True)

    def send_client_acceptance_email(self, auto_accepted=False, rejected=False):

        pdf_content = self.env['ir.actions.report']._render_qweb_pdf("custom_project.action_milestone_report_pdf", self.id)
        filename = f"Milestone_Confirmation_{self.project_id.name or 'report'}.pdf"

        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(pdf_content[0]),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })

        template = self.env.ref("custom_project.milestone_client_accept_email_template")

        # Get emails of operation managers (in CC)
        group = self.env.ref('custom_dashboard.group_dashboard_operation_manager')
        users = self.env['res.users'].search([('groups_id', 'in', [group.id]), ('email', '!=', False)])
        
        # Collect unique emails
        cc_emails = set(user.email for user in users)
        
        if self.project_id.user_id.email:
            cc_emails.add(self.project_id.user_id.email)

        ctx = {
            'auto_accepted': auto_accepted,
            'rejected': rejected,
            'email_cc': ', '.join(cc_emails)
        }

        template.attachment_ids = [(4, attachment.id)]
        template.with_context(ctx).send_mail(self.id, force_send=True)
        template.attachment_ids = [(5, 0, 0)]

    def _cron_auto_accept_pending_milestones(self):
        now = fields.Datetime.now()
        records = self.search([
            ('stage', '=', 'sent'),
            ('token_expiry', '<', now)
        ])
        for rec in records:
            _logger.info(f"Auto-accepting milestone report ID {rec.id}")
            rec.stage = 'accept'
            rec.send_client_acceptance_email(auto_accepted=True)