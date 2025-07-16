
import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError

from markupsafe import Markup
from odoo.tools.mail import is_html_empty

_logger = logging.getLogger(__name__)

PRIORITIES = [
    ("0", "Very Low"),
    ("1", "Low"),
    ("2", "Normal"),
    ("3", "High"),
    ("4", "Very High"),
]
RATING = [
    ("0", "Very Low"),
    ("1", "Low"),
    ("2", "Normal"),
    ("3", "High"),
    ("4", "Very High"),
    ("5", "Extreme High"),
]


class TicketHelpDesk(models.Model):
    """Help_ticket model"""

    _name = "ticket.helpdesk"
    _description = "Helpdesk Ticket"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    def _default_show_create_task(self):
        """Task creation"""
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("odoo_website_helpdesk.show_create_task")
        )

    def _default_show_category(self):
        """Show category default"""
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("odoo_website_helpdesk.show_category")
        )

    ticket_sequence = fields.Char(
        "Name",
        help="Ticket Name",
    )
    tt_id = fields.Char("TT ID")
    employee_id = fields.Many2one(
        "hr.employee", string="Employee", help="Employee", default=lambda self: self.env.user.employee_id
    )
    employee_name = fields.Char("Employee Name", help="Employee Name")
    name = fields.Text("Subject", help="Subject of the Ticket")
    description = fields.Text("Description", help="Description")
    email = fields.Char("Email", help="Email", related="employee_id.work_email")
    phone = fields.Char("Phone", help="Contact Number", related="employee_id.work_phone")

    priority = fields.Selection(
        PRIORITIES, default="1", help="Priority of the" " Ticket"
    )
    stage_id = fields.Many2one(
        "ticket.stage",
        string="Stage",
        default=lambda self: self.env["ticket.stage"]
        .search([("name", "=", "Draft")], limit=1)
        .id,
        tracking=True,
        group_expand="_read_group_stage_ids",
        help="Stages",
    )
    user_id = fields.Many2one(
        "res.users",
        default=lambda self: self.env.user,
        check_company=True,
        index=True,
        tracking=True,
        help="Login User",
        string="User",
    )
    cost = fields.Float("Cost per hour", help="Cost Per Unit")
    create_date = fields.Datetime("Creation Date", help="Created date")
    start_date = fields.Datetime("Start Date", help="Start Date")
    end_date = fields.Datetime("End Date", help="End Date")
    public_ticket = fields.Boolean(string="Public Ticket", help="Public Ticket")
    color = fields.Integer(string="Color", help="Color")
    replied_date = fields.Datetime("Replied date", help="Replied Date")
    last_update_date = fields.Datetime("Last Update Date", help="Last Update Date")

    ticket_type_id = fields.Many2one(
        "helpdesk.type", string="Ticket Type", help="Ticket Type"
    )

    assigned_user_id = fields.Many2one(
        "res.users",
        string="Assigned User",
        help="Assigned User Name",
    )

    user_domain = fields.Char( string="User Domain", help="User Domain", store=True)

    team_id = fields.Many2one(
        "team.helpdesk",
        string="Department",
        help="Helpdesk Team Name",
        store=True,
    )
    team_head_id = fields.Many2one(
        "res.users",
        string="Team Leader", related='team_id.team_lead_id',
        help="Team Leader Name",
        store=True,
    )

    category_id = fields.Many2one(
        "helpdesk.category", string="Category", help="Category"
    )
    tags_ids = fields.Many2many("helpdesk.tag", help="Tags", string="Tags")
    assign_user = fields.Boolean(
        default=False, help="Assign User", string="Assign User"
    )
    attachment_ids = fields.One2many(
        "ir.attachment", "res_id", help="Attachment Line", string="Attachments"
    )
    merge_ticket_invisible = fields.Boolean(
        string="Merge Ticket", help="Merge Ticket Invisible or " "Not", default=False
    )
    merge_count = fields.Integer(string="Merge Count", help="Merged Tickets " "Count")
    active = fields.Boolean(default=True, help="Active", string="Active")

    show_create_task = fields.Boolean(
        string="Show Create Task",
        help="Show created task or not",
        default=_default_show_create_task,
        compute="_compute_show_create_task",
    )
    create_task = fields.Boolean(
        string="Create Task",
        readonly=False,
        help="Create task or not",
        related="team_id.create_task",
        store=True,
    )
    billable = fields.Boolean(
        string="Billable",
        default=False,
        help="Is billable or not",
    )
    show_category = fields.Boolean(
        default=_default_show_category,
        string="Show Category",
        help="Show category or not",
        compute="_compute_show_category",
    )
    employee_rating = fields.Selection(RATING, default="0", readonly=True)
    review = fields.Char("Review", readonly=True, help="Ticket review")
    kanban_state = fields.Selection(
        [
            ("normal", "Ready"),
            ("done", "In Progress"),
            ("blocked", "Blocked"),
        ],
        default="normal",
    )
    website_id = fields.Many2one("website", string="Website", ondelete="cascade")
    company_id = fields.Many2one(
        "res.company", "Company", default=lambda self: self.env.company
    )

    cancel_reason_id = fields.Many2one(
        'ticket.cancel.reason', string='Cancel Reason',
        index=True, ondelete='restrict', tracking=True)

    @api.onchange("team_id")
    def _onchange_team_id(self):
        if self.team_id:
            self.user_domain = f"['|',('id', '=', {self.team_id.team_lead_id.id}),('id', 'in', {self.team_id.member_ids.ids})]"
            print("---------------user_domain", self.user_domain)

    @api.onchange('assigned_user_id')
    def assign_to_teamleader(self):
        """Assigning team leader function"""
        if self.assigned_user_id:
            if self.team_id:
                data_emails = [{"name": record.name, "email": record.email} for record in self.employee_id.job_id.helpdesk_support_manager_ids]
                if self.team_head_id.email not in [item["email"] for item in data_emails]:
                    data_emails.append({"name": self.team_head_id.name, "email": self.team_head_id.email})
                print("--------------------emails", data_emails)
                for record in data_emails:
                    template = self.env.ref('odoo_website_helpdesk.odoo_website_helpdesk_assign')
                    email_values = {'email_to': record.get('email')}
                    body_html = template.body_html
                    body_html = body_html.replace('leader_name', record.get('name'))
                    template.write({'body_html': body_html})
                    template.send_mail(self.id, force_send=True, email_values=email_values)
                self.env.ref('odoo_website_helpdesk.odoo_website_helpdesk_assign_user').send_mail(self.id, force_send=True)
                self.env.ref('odoo_website_helpdesk.odoo_website_helpdesk_to_employee').send_mail(self.id, force_send=True)
                # self.env.ref('odoo_website_helpdesk.odoo_website_helpdesk_assign').send_mail(self.id, force_send=True)
            else:
                raise ValidationError("Please choose a Department")

    def _compute_show_category(self):
        """Compute show category"""
        show_category = self._default_show_category()
        for rec in self:
            rec.show_category = show_category

    def _compute_show_create_task(self):
        """Compute the created task"""
        show_create_task = self._default_show_create_task()
        for record in self:
            record.show_create_task = show_create_task

    def auto_close_ticket(self):
        """Automatically closing the ticket"""
        auto_close = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("odoo_website_helpdesk.auto_close_ticket")
        )
        if auto_close:
            no_of_days = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("odoo_website_helpdesk.no_of_days")
            )
            records = self.env["ticket.helpdesk"].search([])
            for rec in records:
                days = (fields.Datetime.today() - rec.create_date).days
                if days >= int(no_of_days):
                    close_stage_id = self.env["ticket.stage"].search(
                        [("closing_stage", "=", True)]
                    )
                    if close_stage_id:
                        rec.stage_id = close_stage_id

    def default_stage_id(self):
        """Method to return the default stage"""
        return self.env["ticket.stage"].search([("name", "=", "Draft")], limit=1).id

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """
        return the stages to stage_ids
        """
        stage_ids = self.env["ticket.stage"].search([])
        return stage_ids

    @api.model_create_multi
    def create(self, vals_list):
        """Create function"""
        for vals in vals_list:
            if vals.get("ticket_sequence", _("New")) == _("New"):
                vals["ticket_sequence"] = self.env["ir.sequence"].next_by_code("ticket.helpdesk")
        return super(TicketHelpDesk, self).create(vals_list)

    def write(self, vals):
        """Write function"""
        result = super(TicketHelpDesk, self).write(vals)
        return result

    def action_open_merged_tickets(self):
        """Open the merged tickets tree view"""
        ticket_ids = self.env["support.ticket"].search(
            [("merged_ticket", "=", self.id)]
        )
        helpdesk_ticket_ids = ticket_ids.mapped("display_name")
        help_ticket_records = self.env["ticket.helpdesk"].search(
            [("ticket_sequence", "in", helpdesk_ticket_ids)]
        )
        return {
            "type": "ir.actions.act_window",
            "name": "Helpdesk Ticket",
            "view_mode": "tree,form",
            "res_model": "ticket.helpdesk",
            "domain": [("id", "in", help_ticket_records.ids)],
            "context": self.env.context,
        }

    def action_send_reply(self):
        """Opens the email composer with a preloaded reply template if configured."""
        self.ensure_one()  # Ensure the method is called on a single record

        if not self.employee_id:
            raise UserError(_("Please select a employee."))

        # Retrieve the reply template ID from configuration
        template_id = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("odoo_website_helpdesk.reply_template_id")
        )

        try:
            # Convert template_id to an integer if it exists
            template_id = int(template_id) if template_id else None
        except ValueError:
            template_id = None

        # Fetch the mail template
        mail_template = (
            self.env["mail.template"].browse(template_id) if template_id else None
        )

        # Prepare the context for the mail.compose.message wizard
        ctx = {
            "default_model": "ticket.helpdesk",
            "default_res_ids": self.ids,
            "default_composition_mode": "comment",
            "mark_helpdesk_tkt_as_sent": True,
            "default_partner_ids": self.employee_id.ids,
            "force_email": True,
            # "default_email_to": self.email,
        }
        if mail_template and mail_template.exists():
            ctx["default_template_id"] = mail_template.id

        # Return the action to open the mail composer
        return {
            "type": "ir.actions.act_window",
            "name": "Compose Email",
            "res_model": "mail.compose.message",
            "view_mode": "form",
            "target": "new",
            "views": [[False, "form"]],
            "context": ctx,
        }

    @api.returns("mail.message", lambda value: value.id)
    def message_post(self, **kwargs):

        """
            Override message_post function
            For Pass Website ID in mail_post_autofollow for hit mail specific mail server.
        """
        txt_helpdesk_ctx = {
            "mail_post_autofollow": self.env.context.get(
                "mark_helpdesk_tkt_as_sent", True
            ),
            "website_id": self.website_id.id,
        }
        if (
            self.env.context.get("mark_helpdesk_tkt_as_sent")
            and "mail_notify_author" not in kwargs
        ):
            kwargs["notify_author"] = self.env.user.partner_id.id in (
                kwargs.get("partner_ids") or []
            )
        return super(
            TicketHelpDesk, self.with_context(**txt_helpdesk_ctx)
        ).message_post(**kwargs)

    def action_confirm(self):
        # set stage to in progress
        self.write(
            {
                "stage_id": self.env["ticket.stage"]
                .search([("name", "=", "In Progress")], limit=1)
                .id,
                "last_update_date": fields.Datetime.now(),
                "start_date": fields.Datetime.now(),

            }
        )
        self.env.ref("odoo_website_helpdesk.ticket_created").send_mail(self.id, force_send=True)


    def action_close(self):
        # set stage to closed
        if self.assigned_user_id:
            self.write(
                {
                    "stage_id": self.env["ticket.stage"]
                    .search([("name", "=", "Closed")], limit=1)
                    .id,
                    "last_update_date": fields.Datetime.now(),
                    "end_date": fields.Datetime.now(),
                }
            )
            self.env.ref("odoo_website_helpdesk.helpdesk_rating_new").send_mail(self.id, force_send=True)
        else:
            raise UserError(_("There is not assigned user to close the ticket."))

    def action_block(self):
        print("---------------self.email", self.email)
        if self.email:
            self.env['mail.blacklist'].create({'email': self.email})


    def action_cancel(self, **additional_values):
        # set stage to canceled
        print("---------------additional_values", additional_values)
        if self.assigned_user_id:
            if additional_values:
                self.write(dict(additional_values))
            self.write(
                {
                    "stage_id": self.env["ticket.stage"]
                    .search([("name", "=", "Canceled")], limit=1)
                    .id,
                    "last_update_date": fields.Datetime.now(),
                }
            )
            self.env.ref("odoo_website_helpdesk.ticket_canceled").send_mail(self.id, force_send=True)
        else:
            raise UserError(_("There is not assigned user to cancel the ticket."))




class TicketCancelReason(models.TransientModel):
    _name = "ticket.cancel"
    _description = "Ticket Cancel Reason"


    ticket_ids = fields.Many2many('ticket.helpdesk', string='Tickets')
    cancel_reason_id = fields.Many2one('ticket.cancel.reason', 'Cancel Reason')
    cancel_feedback = fields.Html(
        'Cancel Note', sanitize=True
    )

    def action_cancel_reason_apply(self):
        """
        Mark ticket as Cancel and apply the Cancel reason

        :return: dict
        """
        self.ensure_one()
        if not is_html_empty(self.cancel_feedback):
            self.ticket_ids._track_set_log_message(
                Markup('<div style="margin-bottom: 4px;"><p>%s:</p>%s<br /></div>') % (
                    _('Cancel Comment'),
                    self.cancel_feedback
                )
            )
        res = self.ticket_ids.action_cancel(cancel_reason_id=self.cancel_reason_id.id)
        return res


    def action_block_reason_apply(self):
        """
        Mark ticket as Cancel and apply the Cancel reason

        :return: dict
        """
        self.ensure_one()
        if not is_html_empty(self.cancel_feedback):
            self.ticket_ids._track_set_log_message(
                Markup('<div style="margin-bottom: 4px;"><p>%s:</p>%s<br /></div>') % (
                    _('Cancel Comment'),
                    self.cancel_feedback
                )
            )
        print("------------------ticket_ids", self.ticket_ids)
        self.ticket_ids.action_block()
        res = self.ticket_ids.action_cancel(cancel_reason_id=self.cancel_reason_id.id)
        self.ticket_ids.active = False
        return res
