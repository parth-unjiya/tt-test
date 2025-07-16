import datetime
import pymssql
from collections import defaultdict

from odoo import fields, models, api, tools, _
from dateutil import relativedelta
from datetime import datetime, date, timedelta, time

import logging
_logger = logging.getLogger(__name__)


class CustomAttendance(models.Model):
    _inherit = "hr.attendance"

    late_mark = fields.Boolean(string="Late Mark", compute='_late_mark', store=True)
    need_validation = fields.Boolean(string="Need Validation")
    tt_id = fields.Char(string="TT ID")
    punch_in = fields.Datetime(string="Punch In", tracking=True)
    punch_out = fields.Datetime(string="Punch Out", tracking=True)

    lunch_start_time = fields.Datetime(string="Lunch Start Time")
    lunch_end_time = fields.Datetime(string="Lunch End Time")
    actual_lunch_start_time = fields.Datetime(string="Actual Lunch Start Time")
    actual_lunch_end_time = fields.Datetime(string="Actual Lunch End Time")
    lunch_time = fields.Float(string="Lunch Time", compute='_compute_lunch_time', store=True)

    actual_break_start_time = fields.Datetime(string="Actual Break Start Time")
    actual_break_end_time = fields.Datetime(string="Actual Break End Time")
    break_start_time = fields.Datetime(string="Break Start Time")
    break_end_time = fields.Datetime(string="Break End Time")
    break_time = fields.Float(string="Break Time", compute='_compute_break_time', store=True)

    actual_estimate_start_time = fields.Datetime(string="Actual Estimate Start Time")
    actual_estimate_end_time = fields.Datetime(string="Actual Estimate End Time")
    estimate_start_time = fields.Datetime(string="Estimate Start Time")
    estimate_end_time = fields.Datetime(string="Estimate End Time")
    estimate_time = fields.Float(string="Estimate Time", compute='_compute_estimate_time', store=True)

    actual_interview_start_time = fields.Datetime(string="Actual Interview Start Time")
    actual_interview_end_time = fields.Datetime(string="Actual Interview End Time")
    interview_start_time = fields.Datetime(string="Interview Start Time")
    interview_end_time = fields.Datetime(string="Interview End Time")
    interview_time = fields.Float(string="Interview Time", compute='_compute_interview_time', store=True)

    actual_floor_start_time = fields.Datetime(string="Actual Floor Start Time")
    actual_floor_end_time = fields.Datetime(string="Actual Floor End Time")
    floor_start_time = fields.Datetime(string="Floor Start Time")
    floor_end_time = fields.Datetime(string="Floor End Time")
    floor_active_time = fields.Float(string="Floor Active Time", compute='_compute_floor_time', store=True)

    actual_general_meeting_start_time = fields.Datetime(string="Actual General Meeting Start Time")
    actual_general_meeting_end_time = fields.Datetime(string="Actual General Meeting End Time")
    general_meeting_start_time = fields.Datetime(string="General Meeting Start Time")
    general_meeting_end_time = fields.Datetime(string="General Meeting End Time")
    general_meeting_time = fields.Float(string="General Meeting Time", compute='_compute_general_meeting_time', store=True)

    actual_no_work_start_time = fields.Datetime(string="Actual No Work Start Time")
    actual_no_work_end_time = fields.Datetime(string="Actual No Work End Time")
    no_work_start_time = fields.Datetime(string="No Work Start Time")
    no_work_end_time = fields.Datetime(string="No Work End Time")
    no_work_time = fields.Float(string="No Work Time", compute='_compute_no_work_time', store=True)

    actual_r_and_d_start_time = fields.Datetime(string="Actual R & D Start Time")
    actual_r_and_d_end_time = fields.Datetime(string="Actual R & D End Time")
    r_and_d_start_time = fields.Datetime(string="R & D Start Time")
    r_and_d_end_time = fields.Datetime(string="R & D End Time")
    r_and_d_time = fields.Float(string="R & D Time", compute='_compute_r_and_d_time', store=True)

    last_activity_type = fields.Char(string="Last Activity Type")

    user_id = fields.Many2one('res.users', related='employee_id.user_id', string='User')
    reason = fields.Char(string="Reason")



    def action_edit_attendance(self):
        print("\nDebug--------------------action_edit_attendance", self.lunch_start_time, self.lunch_end_time)
        self.ensure_one()
        if self.lunch_start_time and self.lunch_end_time:
            self.actual_lunch_start_time = self.lunch_start_time
            self.actual_lunch_end_time = self.lunch_end_time

        if self.break_start_time and self.break_end_time:
            self.actual_break_start_time = self.break_start_time
            self.actual_break_end_time = self.break_end_time

        if self.estimate_start_time and self.estimate_end_time:
            self.actual_estimate_start_time = self.estimate_start_time
            self.actual_estimate_end_time = self.estimate_end_time

        if self.interview_start_time and self.interview_end_time:
            self.actual_interview_start_time = self.interview_start_time
            self.actual_interview_end_time = self.interview_end_time

        if self.floor_start_time and self.floor_end_time:
            self.actual_floor_start_time = self.floor_start_time
            self.actual_floor_end_time = self.floor_end_time

        if self.general_meeting_start_time and self.general_meeting_end_time:
            self.actual_general_meeting_start_time = self.general_meeting_start_time
            self.actual_general_meeting_end_time = self.general_meeting_end_time

        if self.no_work_start_time and self.no_work_end_time:
            self.actual_no_work_start_time = self.no_work_start_time
            self.actual_no_work_end_time = self.no_work_end_time

        if self.r_and_d_start_time and self.r_and_d_end_time:
            self.actual_r_and_d_start_time = self.r_and_d_start_time
            self.actual_r_and_d_end_time = self.r_and_d_end_time

        action = self.env.ref('custom_attendance.action_edit_attendance').read()[0]
        action['res_id'] = self.id
        action['views'] = [(self.env.ref('custom_attendance.attendance_edit_form_view').id, 'form')]
        action['view_mode'] = 'form'
        return action

    def action_submit_attendance(self):
        """Request validation for attendance."""
        self.write({'need_validation': True})
        partner_list = []
        hr_group = self.env.ref('custom_dashboard.group_dashboard_hr')
        if self.employee_id.parent_id:
            partner_list.append(self.employee_id.parent_id.user_id.partner_id.id)
        partner_list.append(hr_group.users.partner_id.id)
        print("-------------------- partner_list --------------", partner_list)
        self.message_notify(
            partner_ids=partner_list,
            body=f'Please review and approve the change request from {self.user_id.name}.',
            subject='Change Request Approval Needed',
            model='hr.attendance',
            res_id=self.id,
            author_id=self.user_id.partner_id.id,
            record_name=self.name
        )

        _logger.info(f"attendance submitted for validation: {self.employee_id.name}")


    def action_validate_attendance(self):
        """Copy actual times into start/end and mark attendance as validated."""
        for rec in self:
            rec.write({
                'lunch_time': 0 if rec.actual_lunch_start_time and rec.actual_lunch_end_time else rec.lunch_time,
                'lunch_start_time': rec.actual_lunch_start_time if rec.actual_lunch_start_time else rec.lunch_start_time,
                'lunch_end_time': rec.actual_lunch_end_time if rec.actual_lunch_end_time else rec.lunch_end_time,
                'break_time': 0 if rec.actual_break_start_time and rec.actual_break_end_time else rec.break_time,
                'break_start_time': rec.actual_break_start_time if rec.actual_break_start_time else rec.break_start_time,
                'break_end_time': rec.actual_break_end_time if rec.actual_break_end_time else rec.break_end_time,
                'estimate_time': 0 if rec.actual_estimate_start_time and rec.actual_estimate_end_time else rec.estimate_time,
                'estimate_start_time': rec.actual_estimate_start_time if rec.actual_estimate_start_time else rec.estimate_start_time,
                'estimate_end_time': rec.actual_estimate_end_time if rec.actual_estimate_end_time else rec.estimate_end_time,
                'interview_time': 0 if rec.actual_interview_start_time and rec.actual_interview_end_time else rec.interview_time,
                'interview_start_time': rec.actual_interview_start_time if rec.actual_interview_start_time else rec.interview_start_time,
                'interview_end_time': rec.actual_interview_end_time if rec.actual_interview_end_time else rec.interview_end_time,
                'floor_active_time': 0 if rec.actual_floor_start_time and rec.actual_floor_end_time else rec.floor_active_time,
                'floor_start_time': rec.actual_floor_start_time if rec.actual_floor_start_time else rec.floor_start_time,
                'floor_end_time': rec.actual_floor_end_time if rec.actual_floor_end_time else rec.floor_end_time,
                'general_meeting_time': 0 if rec.actual_general_meeting_start_time and rec.actual_general_meeting_end_time else rec.general_meeting_time,
                'general_meeting_start_time': rec.actual_general_meeting_start_time if rec.actual_general_meeting_start_time else rec.general_meeting_start_time,
                'general_meeting_end_time': rec.actual_general_meeting_end_time if rec.actual_general_meeting_end_time else rec.general_meeting_end_time,
                'no_work_time': 0 if rec.actual_no_work_start_time and rec.actual_no_work_end_time else rec.no_work_time,
                'no_work_start_time': rec.actual_no_work_start_time if rec.actual_no_work_start_time else rec.no_work_start_time,
                'no_work_end_time': rec.actual_no_work_end_time if rec.actual_no_work_end_time else rec.no_work_end_time,
                'r_and_d_time': 0 if rec.actual_r_and_d_start_time and rec.actual_r_and_d_end_time else rec.r_and_d_time,
                'r_and_d_start_time': rec.actual_r_and_d_start_time if rec.actual_r_and_d_start_time else rec.r_and_d_start_time,
                'r_and_d_end_time': rec.actual_r_and_d_end_time if rec.actual_r_and_d_end_time else rec.r_and_d_end_time,
                'need_validation': False,
            })
            _logger.info(f"Attendance {rec.employee_id.name} validated for new timings {rec.actual_lunch_start_time} & {rec.actual_lunch_end_time}.")

    def action_cancel_attendance(self):
        """Cancel the attendance validation request."""
        self.write({'need_validation': False})
        _logger.info(f"Attendance(s) cancelled: {[rec.employee_id.name for rec in self]}")


    @api.depends('lunch_end_time')
    def _compute_lunch_time(self):
        for rec in self:
            if rec.lunch_start_time and rec.lunch_end_time:
                rec.lunch_time += (rec.lunch_end_time - rec.lunch_start_time).total_seconds() / 3600
            else:
                rec.lunch_time = 0

    @api.depends('break_end_time')
    def _compute_break_time(self):
        for rec in self:
            if rec.break_start_time and rec.break_end_time:
                rec.break_time += (rec.break_end_time - rec.break_start_time).total_seconds() / 3600
            else:
                rec.break_time = 0

    @api.depends('estimate_end_time')
    def _compute_estimate_time(self):
        for rec in self:
            if rec.estimate_start_time and rec.estimate_end_time:
                rec.estimate_time += (rec.estimate_end_time - rec.estimate_start_time).total_seconds() / 3600
            else:
                rec.estimate_time = 0

    @api.depends('interview_end_time')
    def _compute_interview_time(self):
        for rec in self:
            print("\n\n----Debug--------------------------------------", rec.interview_start_time, rec.interview_end_time, rec.interview_time)
            if rec.interview_start_time and rec.interview_end_time:
                rec.interview_time += (rec.interview_end_time - rec.interview_start_time).total_seconds() / 3600
            else:
                rec.interview_time = 0

    @api.depends('floor_end_time')
    def _compute_floor_time(self):
        for rec in self:
            if rec.floor_start_time and rec.floor_end_time:
                rec.floor_active_time += (rec.floor_end_time - rec.floor_start_time).total_seconds() / 3600
            else:
                rec.floor_active_time = 0

    @api.depends('general_meeting_end_time')
    def _compute_general_meeting_time(self):
        for rec in self:
            if rec.general_meeting_start_time and rec.general_meeting_end_time:
                rec.general_meeting_time += (rec.general_meeting_end_time - rec.general_meeting_start_time).total_seconds() / 3600
            else:
                rec.general_meeting_time = 0

    @api.depends('no_work_end_time')
    def _compute_no_work_time(self):
        for rec in self:
            if rec.no_work_start_time and rec.no_work_end_time:
                rec.no_work_time += (rec.no_work_end_time - rec.no_work_start_time).total_seconds() / 3600
            else:
                rec.no_work_time = 0

    @api.depends('r_and_d_end_time')
    def _compute_r_and_d_time(self):
        for rec in self:
            if rec.r_and_d_start_time and rec.r_and_d_end_time:
                rec.r_and_d_time += (rec.r_and_d_end_time - rec.r_and_d_start_time).total_seconds() / 3600
            else:
                rec.r_and_d_time = 0



    @api.depends('punch_in')
    def _late_mark(self):
        for rec in self:
            if not rec.late_mark and rec.punch_in:
                current_date = datetime.today()
                print(current_date.year, rec.create_date.year)
                if rec.create_date.year == current_date.year and rec.create_date.month == current_date.month and rec.create_date.day == current_date.day:
                    print("--------iddd")
                    valid_time = (datetime.today() + relativedelta.relativedelta(hour=10,
                                                                                             minute=10)) - relativedelta.relativedelta(
                        hours=5, minutes=30)
                    if rec.punch_in > valid_time:
                        print("iffff")
                        rec.late_mark = True
                    else:
                        rec.late_mark = False
                else:
                    rec.late_mark = False



    # @api.model
    # def _attendance_email(self):
    #     # print(">>>.called", self.id, self.env.context)
    #     current_date = ((datetime.today() + relativedelta.relativedelta(hour=10,
    #                                                                              minute=30)) - relativedelta.relativedelta(
    #         hours=5, minutes=30))
    #     data = self.env['hr.attendance'].search([('check_in', '>', current_date)])
    #     dataset = []
    #     for rec in data:
    #         late_count = self.env['hr.attendance'].search_count(
    #             [('late_mark', '=', True), ('employee_id', '=', rec.employee_id.id)])
    #         print(late_count)
    #         record_dict = {
    #             'check_in': rec.check_in if hasattr(rec, 'check_in') else None,
    #             'employee': rec.employee_id.name if hasattr(rec.employee_id, 'name') else None,
    #             'employee_code': rec.employee_id.barcode if hasattr(rec.employee_id, 'barcode') else None,
    #             'department': rec.employee_id.department_id.name if hasattr(rec.employee_id,
    #                                                                         'department_id') and hasattr(
    #                 rec.employee_id.department_id, 'name') else None,
    #             'shift': rec.employee_id.resource_calendar_id.attendance_ids[0].hour_from if hasattr(rec.employee_id,
    #                                                                                                  'resource_calendar_id') and hasattr(
    #                 rec.employee_id.resource_calendar_id,
    #                 'name') and hasattr(rec.employee_id.resource_calendar_id.attendance_ids[0], 'hour_from') else None,
    #             'company': rec.employee_id.company_id.name if hasattr(rec.employee_id, 'company_id') and hasattr(
    #                 rec.employee_id.company_id, 'name') else None,
    #             'late_count': late_count if late_count else None,

    #         }
    #         dataset.append(record_dict)
    #     print(dataset)

    #     rendered_body = self.env['mail.render.mixin']._render_template(
    #         'custom_attendance.attendance_template',
    #         'hr.attendance',
    #         self.ids,
    #         engine='qweb_view',
    #         options={
    #             'preserve_comments': True,
    #             'post_process': True,
    #         },
    #     )
    #     full_mail = self.env['mail.render.mixin']._render_encapsulate(
    #         'custom_attendance.attendance_template',
    #         rendered_body,
    #         add_context={
    #             'data': dataset,
    #             'user': self.env.user,
    #         },
    #     )
    #     print(full_mail)

    #     # rendered_template = mail_template.send_mail(self.id)
    #     # print(rendered_template)

    #     mail_values = {
    #         'author_id': self.env.user.partner_id.id,
    #         'email_from': 'your@email.com',
    #         'email_to': 'recipient@email.com',
    #         'subject': "Daily Report",
    #         'body_html': full_mail,
    #         'state': 'outgoing',
    #     }

    #     self.env['mail.mail'].sudo().create(mail_values)


    @api.model
    def get_absentees_details(self):
        today = date.today()
        first_day_of_month = today.replace(day=1)

        all_employees = self.env['hr.employee'].sudo().search_read(
            [('active', '=', True)],
            ['id', 'emp_code', 'name', 'department_id', 'company_id']
        )

        leave_employees = set(self.env['hr.leave'].sudo().search([
            ('state', '=', 'validate'),
            ('date_from', '<=', today),
            ('date_to', '>=', today)
        ]).mapped('employee_id.id'))

        attended_employees = set(self.env['hr.attendance'].sudo().search([
            ('check_in', '>=', today.strftime('%Y-%m-%d 00:00:00')),
            ('check_in', '<=', today.strftime('%Y-%m-%d 23:59:59'))
        ]).mapped('employee_id.id'))

        absentees_list = []
        sr_no = 1

        for employee in all_employees:
            emp_id = employee['id']

            if emp_id not in leave_employees and emp_id not in attended_employees:
                total_leaves_this_month = self.env['hr.leave'].sudo().search_count([
                    ('employee_id', '=', emp_id),
                    ('state', '=', 'validate'),
                    ('date_from', '>=', first_day_of_month),
                    ('date_to', '<=', today)
                ])

                absentees_list.append({
                    'id': emp_id,
                    'sr_no': sr_no,
                    'emp_code': employee.get('emp_code', "N/A"),
                    'name': employee.get('name', "N/A"),
                    'department': self.env['hr.department'].browse(employee.get('department_id')[0]).name if employee.get('department_id') else "N/A",
                    'company': self.env['res.company'].browse(employee.get('company_id')[0]).name if employee.get('company_id') else "N/A",
                    'is_absent': True,
                    'leave_applied': False,
                    'leave_current_month': total_leaves_this_month,
                    'attendance_recorded': False,
                    'absence_date': today.strftime('%d-%m-%Y'),
                })
                sr_no += 1

        return absentees_list


    @api.model
    def _attendance_email(self):
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        attendance_records = self.env['hr.attendance'].search([('check_in', '>=', today)])
        lateness_data = []

        for rec in attendance_records:
            employee = rec.employee_id
            calendar = employee.resource_calendar_id
            shift_time = calendar.attendance_ids[0].hour_from if calendar and calendar.attendance_ids else None

            late_count = self.env['hr.attendance'].search_count([
                ('late_mark', '=', True),
                ('employee_id', '=', employee.id)
            ])

            lateness_data.append({
                'employee': employee.name,
                'employee_code': employee.emp_code,
                'department': employee.department_id.name if employee.department_id else "N/A",
                'shift': shift_time,
                'company': employee.company_id.name if employee.company_id else "",
                'late_count': late_count,
            })

        # Get absentees data
        absentees_data = self.get_absentees_details()

        # Render QWeb template
        body_html = self.env['ir.qweb']._render(
            'custom_attendance.attendance_template',
            values={
                'lateness_data': lateness_data,
                'absentees_data': absentees_data,
                'user': self.env.user,
            }
        )

        self.env['mail.mail'].sudo().create({
            'author_id': self.env.user.partner_id.id,
            'email_from': self.env.user.email or 'noreply@example.com',
            'email_to': 'recipient@example.com',
            'subject': "Daily Attendance Report",
            'body_html': body_html,
        }).send()


    @api.model
    def auto_checkout_attendances(self):
        print("\n\n========== Auto Check-Out Process Started ==========\n")

        today = datetime.now().date()
        start_of_day = today.strftime("%Y-%m-%d 00:00:00")
        end_of_day = today.strftime("%Y-%m-%d 23:59:59")
        checkout_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"Date: {today}")
        print(f"Time Range: {start_of_day} → {end_of_day}")
        print(f"Auto Check-Out Time: {checkout_time}")

        records = self.sudo().search([
            ("check_in", ">=", start_of_day),
            ("check_in", "<=", end_of_day),
            ('check_out', '=', False)
        ])

        print(f"\nFound {len(records)} attendance record(s) without check-out.\n")

        for rec in records:
            rec.check_out = checkout_time
            print(f"Checked out: {rec.employee_id.name} | Check-in: {rec.check_in} → Check-out: {checkout_time}")

        print("\n========== Auto Check-Out Process Completed ==========\n")

    
    @api.model
    def fetch_biometric_attendance(self):
        # Get current time in IST
        ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
        current_time = ist_now.time()

        # Run only if time is between 8-11:30 AM or 12-3 PM or 5-10 PM
        if not (
            (time(9, 0) <= current_time < time(11, 0)) or
            (time(13, 0) <= current_time < time(15, 0)) or
            (time(17, 0) <= current_time < time(22, 0))
        ):
            _logger = self.env['ir.logging']
            _logger.sudo().create({
                'name': 'Biometric Sync',
                'type': 'server',
                'level': 'info',
                'message': f'Skipped biometric sync at {current_time}. Outside allowed time window.',
                'path': __name__,
                'func': 'fetch_biometric_attendance',
                'line': 0,
            })
            return  # Exit early if not in desired time window

        print(f"\n\n========== Fetch Biometric Attendance Process Started {current_time} ==========\n")
        
        # Get config
        config = self.env["ir.config_parameter"].sudo()
        server = config.get_param('biometric.server') or ""
        user = config.get_param('biometric.user') or ""
        password = config.get_param('biometric.password') or ""
        database = config.get_param('biometric.database') or ""
        
        try:
            conn = pymssql.connect(
                server=server,
                user=user,
                password=password,
                database=database
            )
            cursor = conn.cursor()

            # Define today and yesterday in IST
            today = ist_now.date()
            yesterday = today - timedelta(days=1)

            # Fetch data for yesterday and today
            dates_to_fetch = [yesterday, today]
            all_rows = []

            for target_date in dates_to_fetch:
                cursor.execute("""
                    SELECT CARDNO, S_DateTime, D_DateTime
                    FROM TRANSACTIONS
                    WHERE CAST(S_DateTime AS DATE) = %s
                """, (target_date,))
                rows = cursor.fetchall()
                all_rows.extend(rows)

            conn.close()

            # Group entries by (employee barcode, date)
            records = defaultdict(list)
            for cardno, s_dt, d_dt in all_rows:
                if not s_dt:
                    continue
                s_utc = s_dt - timedelta(hours=5,  minutes=30)
                records[(cardno, s_utc.date())].append(s_utc)

            for (cardno, date), times in records.items():
                employee = self.env['hr.employee'].search([('emp_code', '=', cardno)], limit=1)
                if not employee:
                    continue

                times.sort()
                punch_in = times[0]
                punch_out = times[1] if len(times) > 1 else None

                # Late mark logic
                ist_punch_in = punch_in + timedelta(hours=5, minutes=30)
                is_late = ist_punch_in.time() > time(10, 10)

                # Check for existing attendance on that date
                existing = self.search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '>=', datetime.combine(date, time.min)),
                    ('check_in', '<=', datetime.combine(date, time.max)),
                ], limit=1)

                if existing:
                    vals = {}
                    if not existing.check_out and punch_out:
                        vals.update({'check_out': punch_out})
                    if punch_out:
                        vals.update({'punch_out': punch_out})
                    if not existing.punch_in:
                        vals.update({
                            'punch_in': punch_in,
                            'late_mark': is_late,
                        })
                    if vals:
                        existing.write(vals)
                else:
                    self.create({
                        'employee_id': employee.id,
                        'check_in': punch_in,
                        'punch_in': punch_in,
                        'check_out': punch_out,
                        'punch_out': punch_out,
                        'late_mark': is_late,
                    })

        except Exception as e:
            _logger = self.env['ir.logging']
            _logger.sudo().create({
                'name': 'Biometric Sync',
                'type': 'server',
                'level': 'error',
                'message': f'Biometric sync failed: {e}',
                'path': __name__,
                'func': 'fetch_biometric_attendance',
                'line': 0,
            })






    # @api.model
    # def fetch_biometric_attendance(self):
    #     # Get current time in IST
    #     ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
    #     current_time = ist_now.time()

    #     # Run only if time is between 8-11:30 AM or 12-3 PM or 5-8 PM
    #     if not (
    #         (time(8, 0) <= current_time < time(11, 30)) or
    #         (time(12, 0) <= current_time < time(15, 0)) or
    #         (time(17, 0) <= current_time < time(22, 0))
    #     ):
    #         _logger = self.env['ir.logging']
    #         _logger.sudo().create({
    #             'name': 'Biometric Sync',
    #             'type': 'server',
    #             'level': 'info',
    #             'message': f'Skipped biometric sync at {current_time}. Outside allowed time window.',
    #             'path': __name__,
    #             'func': 'fetch_biometric_attendance',
    #             'line': 0,
    #         })
    #         return  # Exit early if not in desired time window

    #     print(f"\n\nDEBUG: Fetch Biometric Attendance Process Started {current_time}\n")
    #     # Get config
    #     config = self.env["ir.config_parameter"].sudo()
    #     server = config.get_param('biometric.server') or ""
    #     user = config.get_param('biometric.user') or ""
    #     password = config.get_param('biometric.password') or ""
    #     database = config.get_param('biometric.database') or ""
    #     try:
    #         conn = pymssql.connect(
    #             server=server,
    #             user=user,
    #             password=password,
    #             database=database
    #         )

    #         cursor = conn.cursor()

    #         # Current date in IST
    #         # ist_now = datetime.now() + timedelta(hours=5, minutes=30)
    #         today = ist_now.date()

    #         # Yesterday's date in IST
    #         # today_ist = datetime.now() - timedelta(days=2, hours=5, minutes=30)
    #         # today_date = today_ist.date()

    #         # Fetch today's records
    #         cursor.execute("""
    #             SELECT CARDNO, S_DateTime, D_DateTime
    #             FROM TRANSACTIONS
    #             WHERE CAST(S_DateTime AS DATE) = %s
    #         """, (today,))
    #         rows = cursor.fetchall()
    #         conn.close()

    #         # Group entries by (employee barcode, date)
    #         records = defaultdict(list)
    #         for cardno, s_dt, d_dt in rows:
    #             if not s_dt:
    #                 continue
    #             s_utc = s_dt - timedelta(hours=5,  minutes=30)
    #             records[(cardno, s_utc.date())].append(s_utc)

    #         for (cardno, date), times in records.items():
    #             employee = self.env['hr.employee'].search([('emp_code', '=', cardno)], limit=1)
    #             if not employee:
    #                 continue

    #             times.sort()
    #             punch_in = times[0]
    #             punch_out = times[1] if len(times) > 1 else None

    #             # Late mark logic
    #             ist_punch_in = punch_in + timedelta(hours=5, minutes=30)
    #             is_late = ist_punch_in.time() > time(10, 10)

    #             # Check for existing attendance on that date
    #             existing = self.search([
    #                 ('employee_id', '=', employee.id),
    #                 ('check_in', '>=', datetime.combine(date, time.min)),
    #                 ('check_in', '<=', datetime.combine(date, time.max)),
    #             ], limit=1)

    #             if existing:
    #                 # Update only if punch_out is new
    #                 vals = {}
    #                 if not existing.check_out and punch_out:
    #                     vals.update({
    #                         'check_out': punch_out,
    #                     })

    #                 if punch_out:
    #                     vals.update({
    #                         'punch_out': punch_out,  
    #                     })

    #                 if not existing.punch_in:
    #                     vals.update({
    #                         # 'check_in': punch_in,
    #                         'punch_in': punch_in,
    #                         'late_mark': is_late,
    #                     })
    #                 if vals:
    #                     existing.write(vals)
    #             else:
    #                 self.create({
    #                     'employee_id': employee.id,
    #                     'check_in': punch_in,
    #                     'punch_in': punch_in,
    #                     'check_out': punch_out,
    #                     'punch_out': punch_out,
    #                     'late_mark': is_late,
    #                 })

    #     except Exception as e:
    #         _logger = self.env['ir.logging']
    #         _logger.sudo().create({
    #             'name': 'Biometric Sync',
    #             'type': 'server',
    #             'level': 'error',
    #             'message': f'Biometric sync failed: {e}',
    #             'path': __name__,
    #             'func': 'fetch_biometric_attendance',
    #             'line': 0,
    #         })