from odoo import models, fields, api
from datetime import datetime, timedelta, time


class ResUsers(models.Model):
    _name = 'work.report'

    yesterday_attendance = fields.One2many(
        'hr.attendance', 'user_id',
        string="Yesterday's Attendance",
        domain=lambda self: self._get_yesterday_attendance_domain()
    )

    yesterday_timesheets = fields.One2many(
        'account.analytic.line', 'user_id',
        string="Yesterday's Timesheets",
        domain=lambda self: self._get_yesterday_timesheet_domain()
    )

    timesheet_backup = fields.Text(string="Backup Timesheets")
    attendance_backup = fields.Text(string="Backup Attendance")

    def _get_yesterday_attendance_domain(self):
        yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()
        print("\nDebug--------------------yesterday", yesterday)
        return [('check_in', '>=', f'{yesterday} 00:00:00'), ('check_in', '<=', f'{yesterday} 23:59:59')]

    def _get_yesterday_timesheet_domain(self):
        yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()
        print("\nDebug--------------------yesterday timesheet", yesterday)
        return [('date', '=', yesterday)]


    editable_window = fields.Boolean(compute='_compute_editable_window', store=False)

    @api.depends_context('tz')
    def _compute_editable_window(self):
        for user in self:
            # Get current datetime in user timezone
            now_dt = fields.Datetime.context_timestamp(user, fields.Datetime.now())
            now_time = now_dt.time()
            print("\nDebug--------------------now_time", now_time)

            # Define your window
            start_time = time(10, 0)
            print("\nDebug--------------------start_time", start_time)
            end_time = time(20, 0)
            print("\nDebug--------------------end_time", end_time)

            # Check if current time is in range
            user.editable_window = start_time <= now_time <= end_time
            print("\nDebug--------------------user.editable_window", user.editable_window)

    def action_submit_to_manager(self):
        for user in self:
            print("\nDebug--------------------user", user)
            # user.change_approval_state = 'pending'

            # Backup current values
            user.timesheet_backup = {
                line.id: {
                    'name': line.name,
                    'unit_amount': line.unit_amount,
                    # Add more fields as needed
                } for line in user.yesterday_timesheets
            }

            user.attendance_backup = {
                att.id: {
                    'check_in': str(att.check_in),
                    'check_out': str(att.check_out),
                } for att in user.yesterday_attendance
            }

            print("\nDebug--------------------user.timesheet_backup", user.timesheet_backup)
            print("\nDebug--------------------user.attendance_backup", user.attendance_backup)

            # Notify manager and HR
            partners = user._get_notify_partners()
            user.message_post(
                body=f"<p><b>{user.name}</b> has requested timesheet/attendance changes.</p>",
                partner_ids=partners.ids,
                subject="Request for Approval"
            )
