from odoo import models, fields, api
from datetime import datetime, timedelta, time
import logging

_logger = logging.getLogger(__name__)



class AccountAnalyticLine(models.Model):
    _name = 'account.analytic.line'
    _inherit = ['account.analytic.line', 'mail.thread']

    tt_id = fields.Char(string="TT ID")
    start_time = fields.Datetime(string="Start Time")
    end_time = fields.Datetime(string="End Time")
    unit_hours = fields.Float(
        'Unit Hours',
        default=0.0, store=True,
        compute="_compute_duration_time"
    )

    actual_start_time = fields.Datetime(string="Actual Start Time")
    actual_end_time = fields.Datetime(string="Actual End Time")
    reason = fields.Char(string="Reason")
    need_validation = fields.Boolean(string="Need Validation")


    @api.depends('end_time')
    def _compute_duration_time(self):
        for rec in self:
            if rec.start_time and rec.end_time: 
                rec.unit_hours = (rec.end_time - rec.start_time).total_seconds() / 3600
                rec.unit_amount = rec.unit_hours
            else:
                rec.unit_hours = rec.unit_hours


    def action_edit_timesheet(self):
        print("\nDebug--------------------action_edit_timesheet")
        self.ensure_one()

        self.actual_start_time = self.start_time
        self.actual_end_time = self.end_time

        action = self.env.ref('custom_project.action_edit_timesheet').read()[0]
        action['res_id'] = self.id
        action['views'] = [(self.env.ref('custom_project.timesheet_edit_form_view').id, 'form')]
        action['view_mode'] = 'form'
        return action

    def action_validate_timesheet(self):
        """Copy actual times into start/end and mark timesheet as validated."""
        for rec in self:
            rec.write({
                'start_time': rec.actual_start_time,
                'end_time': rec.actual_end_time,
                'need_validation': False,
            })
            _logger.info(f"Timesheet {rec.name} validated for new timings {rec.actual_start_time} → {rec.actual_end_time}.")

    def action_cancel_timesheet(self):
        """Cancel the timesheet validation request."""
        self.write({'need_validation': False})
        _logger.info(f"Timesheet(s) cancelled: {[rec.name for rec in self]}")

    def action_submit_timesheet(self):
        """Request validation for timesheet."""
        self.write({'need_validation': True})

        partner_list = []
        hr_group = self.env.ref('custom_dashboard.group_dashboard_hr')
        if self.employee_id.parent_id:
            partner_list.append(self.employee_id.parent_id.user_id.partner_id.id)
        partner_list.append(hr_group.users.partner_id.id)
        print("-------------------- partner_list --------------", partner_list)
        self.message_notify(
            partner_ids=partner_list,
            body=f'Please review and approve the change request from {self.employee_id.name}.',
            subject='Change Request Approval Needed',
            model='account.analytic.line',
            res_id=self.id,
            author_id=self.employee_id.user_id.partner_id.id,
            record_name=self.name
        )

        _logger.info(f"Timesheet submitted for validation: {self.name}")