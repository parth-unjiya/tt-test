from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    state = fields.Selection(
        selection_add=[
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ], ondelete={'approved': 'cascade', 'rejected': 'cascade'}
    )

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_rejected(self):
        self.write({'state': 'rejected'})

    @api.model
    def trigger_notification(self):
        # Fetch the OdooBot partner
        odoobot_partner = self.env['res.partner'].search([('name', '=', 'OdooBot'), ('active', '=', False)], limit=1)
        print("Debug------------------------ odoobot_partner ----------------------->", odoobot_partner)
        if not odoobot_partner:
            print("OdooBot partner not found!")
            return False
        # Get the group
        group = self.env.ref('custom_dashboard.group_dashboard_resource_manager')
        print("Debug------------------------ group ----------------------->", group)

        # Fetch users belonging to the specified group
        user_ids = self.env['res.users'].search([('groups_id', 'in', [group.id])])
        print("Debug------------------------ user_ids ----------------------->", user_ids)

        for user in user_ids:
            # Create the notification
            user_partner = user.partner_id

            # Search for the channel between OdooBot and the user
            channel = self.env['discuss.channel'].search([
                ('channel_partner_ids', 'in', [odoobot_partner.id]),
                ('channel_partner_ids', 'in', [user_partner.id]),
            ], limit=1)

            print("Debug------------------------ channel ----------------------->", channel)

            self.message_notify(
                partner_ids=[user_partner.id],
                subject='New Invoice has been requested',
                body=f'New Invoice for {self.partner_id.name} has been requested.',
                res_id=self.id,
                model='resource.allocation',
                author_id=odoobot_partner.id,
                record_name=self.name,
            )

    def action_post(self):
        res = super(AccountMove, self).action_post()
        self.trigger_notification()
        return res


    def send_invoice_creation_notification(self):
        odoobot = self.env['res.partner'].sudo().search([
            ('name', '=', 'OdooBot'), ('active', '=', False)
        ], limit=1)

        print("Debug------------------------ odoobot ----------------------->", odoobot)

        if not odoobot:
            _logger.warning("OdooBot not found.")
            return

        group = self.env.ref('custom_dashboard.group_dashboard_resource_manager_assistant')  # use your group XML ID
        users = self.env['res.users'].sudo().search([('groups_id', 'in', [group.id])])
        print("Debug------------------------ users ----------------------->", users)
        for user in users:
            self.message_notify(
                partner_ids=[user.partner_id.id],
                subject='New Invoice Created',
                body=f'Invoice {self.name} has been created from a Milestone: {self.line_ids.sale_line_ids[0].name}',
                model=self._name,
                res_id=self.id,
                author_id=odoobot.id,
                record_name=self.name,
            )