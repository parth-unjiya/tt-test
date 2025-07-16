from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HrSandwichLeaveRule(models.Model):
    _name = "hr.sandwich.leave.rule"
    rec_name = "leave_type_id"
    _description = "Sandwich Leave Rule Configuration"

    leave_type_id = fields.Many2one(
        "hr.leave.type",
        string="Leave Type",
        required=True,
        help="Select the type of leave this rule applies to.",
    )
    notice_period_days = fields.Integer(
        string="Minimum Notice Period (Days)",
        default=7,
        help="Minimum number of days required to apply for leave in advance.",
    )
    include_weekends = fields.Boolean(
        string="Include Weekends",
        default=True,
        help="If checked, weekends (Saturday & Sunday) will be counted as leave days.",
    )
    include_public_holidays = fields.Boolean(
        string="Include Public Holidays",
        default=True,
        help="If checked, public holidays falling within the leave period will be counted.",
    )
    medical_certificate_required = fields.Boolean(
        string="Require Medical Certificate",
        default=False,
        help="If checked, employees must provide a medical certificate for certain leave types.",
    )
    max_exemptions_per_year = fields.Integer(
        string="Max Exemptions Per Year",
        default=1,
        help="Maximum times an employee can be exempted from the sandwich rule per year.",
    )

    @api.constrains('notice_period_days')
    def _check_notice_period_days(self):
        for record in self:
            if record.notice_period_days < 0:
                raise ValidationError("Notice period days cannot be negative.")