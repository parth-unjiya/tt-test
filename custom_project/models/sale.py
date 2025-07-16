from odoo import models, fields, api


class SalesOrder(models.Model):
    _inherit = "sale.order"

    lead_mapping_id = fields.Char(string="Lead Mapping Id")

    partner_bank_id = fields.Many2one(
        "res.partner.bank",
        string="Recipient Bank",
        help="Bank Account Number to which the invoice will be paid. "
        "A Company bank account if this is a Customer Invoice or Vendor Credit Note, "
        "otherwise a Partner bank account number.",
        check_company=True,
        tracking=True,
        ondelete="restrict",
    )

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()

        # Inject partner_bank_id from Sale Order
        if self.partner_bank_id:
            invoice_vals['partner_bank_id'] = self.partner_bank_id.id

        if self.commitment_date:
            invoice_vals['delivery_date'] = self.commitment_date

        return invoice_vals


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"


    deadline = fields.Date(string="Milestone Deadline", required=True)

    def _timesheet_create_project_prepare_values(self):
        """Override to customize the generated project values"""
        values = super()._timesheet_create_project_prepare_values()

        # Custom logic to change project name
        custom_name = f"{self.order_id.partner_id.name}'s Project"
        values["name"] = custom_name

        return values

    def _generate_milestone(self):
        if self.product_id.service_policy == 'delivered_milestones':
            milestone = self.env['project.milestone'].create({
                'name': self.name,
                'project_id': self.project_id.id or self.order_id.project_id.id,
                'sale_line_id': self.id,
                'quantity_percentage': 1,
                'deadline': self.deadline
            })
            if self.product_id.service_tracking == 'task_in_project':
                self.task_id.milestone_id = milestone.id

    @api.onchange('deadline')
    def _change_date_deadline(self):
        self.ensure_one()
        milestone_obj = self.env['project.milestone'].search([('sale_line_id','=', self._origin.id)])
        if milestone_obj:
            milestone_obj.deadline = self.deadline
