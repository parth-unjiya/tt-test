# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError


class ProjectMilestone(models.Model):
    _inherit = "project.milestone"

    amount = fields.Float(
        string="Amount",
        help="Amount of this milestone. Used to compute percentage based on sale line subtotal.",
        related="sale_line_id.price_unit",
    )

    invoice_name = fields.Char(
            string="Invoice Number",
            compute="_compute_invoice_info",
            store=False
        )

    invoice_status = fields.Char(
        string="Invoice Status",
        compute="_compute_invoice_info",
        store=False
    )

    @api.depends("sale_line_id.invoice_lines.move_id")
    def _compute_invoice_info(self):
        """
        Compute invoice name and status from the first related invoice line.
        """
        for rec in self:
            invoice_line = rec.sale_line_id.invoice_lines.filtered(lambda l: l.move_id)[:1]
            if invoice_line:
                rec.invoice_name = invoice_line.move_id.name
                rec.invoice_status = invoice_line.move_id.state
            else:
                rec.invoice_name = False
                rec.invoice_status = False

    def create_invoice_from_sale_line(self):

        this = self.sudo()
        this.ensure_one()

        # Check if milestone is linked to a sale line
        if not this.sale_line_id:
            raise UserError("No sale line associated with this milestone.")

        # Ensure the sale line is linked to a sale order
        sale_order = this.sale_line_id.order_id
        if not sale_order:
            raise UserError("No sale order associated with this sale line.")

        # Prevent duplicate invoice creation if already invoiced
        if this.sale_line_id.qty_invoiced == 1:
            raise UserError(f"The milestone '{this.name}' has already been fully invoiced.")

        # Create invoice
        invoice = sale_order._create_invoices()
        invoice.send_invoice_creation_notification()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Invoice Created',
                'message': f"Invoice {invoice.name} has been created for milestone: {this.name}",
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.client', 'tag': 'reload'},
            }
        }

    def unlink(self):
        if not self.env.user.has_group('project.group_project_manager'):
            raise UserError("You do not have permission to delete milestones.")
        return super(ProjectMilestone, self).unlink()
