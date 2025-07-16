import logging

from odoo import models, fields, api
from datetime import datetime, timedelta, time, date

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'


    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + [
            'yesterday_attendance', 'yesterday_timesheets'
        ]

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + [
            'yesterday_timesheets', 'yesterday_attendance'
        ]

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

    user_role = fields.Selection([
        ('qa', 'QA'),
        ('developer', 'Developer'),
        ('hr', 'HR'),
        ('project_manager', 'Project Manager'),
        ('operation_manager', 'Operation Manager'),
        ('resource_manager', 'Resource Manager'),
        ('resource_manager_assistant', 'Resource Manager Assistant'),
        ('account_department', 'Account Department'),
        ('network_department', 'Network Admin'),
    ], string='User Role', default='developer')


    def assign_groups_by_role(self):
        """Assign only the groups related to the selected role, removing all others."""
        role_group_map = {
            'qa': [
                'base.group_user',
                'project.group_project_user',
                'hr_timesheet.group_hr_timesheet_user',
                'custom_recruitment.group_hr_recruitment_my_referral',
                'employee_handover.group_technique_user',
                'hr_appraisal.oh_appraisal_group_employee',
                'odoo_website_helpdesk.helpdesk_user',
                'custom_dashboard.group_dashboard_employee',
            ],

            'developer': [
                'base.group_user',
                'project.group_project_user',
                'hr_timesheet.group_hr_timesheet_user',
                'custom_recruitment.group_hr_recruitment_my_referral',
                'employee_handover.group_technique_user',
                'hr_appraisal.oh_appraisal_group_employee',
                'odoo_website_helpdesk.helpdesk_user',
                'custom_dashboard.group_dashboard_employee',
            ],

            'hr': [
                'base.group_user',
                'hr.group_hr_user',
                'hr_contract.group_hr_contract_employee_manager',
                'hr_holidays.group_hr_holidays_user',
                'hr_recruitment.group_hr_recruitment_user',
                'hr_attendance.group_hr_attendance_officer',
                'employee_handover.group_technique_hr',
                'hr_appraisal.oh_appraisal_group_user',
                'custom_dashboard.group_dashboard_hr',
                'odoo_website_helpdesk.helpdesk_team_leader',
            ],
            'project_manager': [
                'base.group_user',
                'custom_project.group_project_manager_limited',
                'hr_timesheet.group_hr_timesheet_user',
                'custom_recruitment.group_hr_recruitment_my_referral',
                'employee_handover.group_technique_user',
                'hr_appraisal.oh_appraisal_group_employee',
                'odoo_website_helpdesk.helpdesk_user',
                'custom_dashboard.group_dashboard_project_manager',
            ],
            'operation_manager': [
                'base.group_user',
                'project.group_project_manager',
                'hr_timesheet.group_hr_timesheet_user',
                'custom_recruitment.group_hr_recruitment_my_referral',
                'employee_handover.group_handover_manager',
                'hr_appraisal.oh_appraisal_group_manager',
                'odoo_website_helpdesk.helpdesk_manager',
                'custom_dashboard.group_dashboard_operation_manager',
            ],
            'resource_manager': [
                'base.group_user',
                'project.group_project_manager',
                'hr_timesheet.group_hr_timesheet_user',
                'custom_recruitment.group_hr_recruitment_my_referral',
                'employee_handover.group_handover_manager',
                'hr_appraisal.oh_appraisal_group_manager',
                'odoo_website_helpdesk.helpdesk_manager',
                'custom_dashboard.group_dashboard_resource_manager',
            ],
            'account_department': [
                'base.group_user',
                'hr_timesheet.group_hr_timesheet_user',
                'account.group_account_user',
                'account.group_account_invoice',
                'custom_recruitment.group_hr_recruitment_my_referral',
                'employee_handover.group_technique_user',
                'hr_appraisal.oh_appraisal_group_employee',
                'odoo_website_helpdesk.helpdesk_user',
                'custom_dashboard.group_dashboard_employee',
            ],
            'network_department': [
                'base.group_user',
                'project.group_project_user',
                'hr_timesheet.group_hr_timesheet_user',
                'custom_recruitment.group_hr_recruitment_my_referral',
                'employee_handover.group_technique_user',
                'hr_appraisal.oh_appraisal_group_employee',
                'odoo_website_helpdesk.helpdesk_team_leader',
                'custom_dashboard.group_dashboard_employee',
            ],
        }

        for user in self:

            if user.id == 2:
                _logger.info("Skipping group update for user ID 2: %s", user.name)
                continue



            role_groups = role_group_map.get(user.user_role, [])

            # Resolve XML IDs to group records
            group_ids = [
                self.env.ref(xml_id, raise_if_not_found=False).id
                for xml_id in role_groups
                if self.env.ref(xml_id, raise_if_not_found=False)
            ]

            # Remove all other groups and assign only relevant ones
            user.groups_id = [(6, 0, group_ids)]
            _logger.info("Groups set for user %s (ID=%s): %s", user.name, user.id, role_groups)

    @api.model_create_multi
    def create(self, vals):
        user = super().create(vals)
        print("\nDebug--------------------user", vals)
        if vals[0].get('user_role') and user.id != 2:
            user.assign_groups_by_role()
        return user

    def write(self, vals):
        res = super().write(vals)
        if 'user_role' in vals:
            for user in self:
                if user.id != 2:
                    user.assign_groups_by_role()
        return res

    def _get_yesterday_attendance_domain(self):
        try:
            current_day = date.today().strftime("%A")
            print("\nDebug--------------------current_day", current_day,date.today(), self.env.user.employee_id.id)
            if current_day != 'Monday':
                yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()
            else:
                object_attendance = self.env['hr.attendance'].sudo().search([('create_date', '!=', date.today()), ('employee_id', '=', self.env.user.employee_id.id)], limit=1, order='create_date desc')
                print("\nDebug--------------------object_attendance", object_attendance)
                yesterday = object_attendance.check_in.date().isoformat()
            print("\nDebug--------------------yesterday", yesterday)
            return [('check_in', '>=', f'{yesterday} 00:00:00'), ('check_in', '<=', f'{yesterday} 23:59:59')]
        except Exception as e:
            print("\nDebug--------------------Error", e)


    def _get_yesterday_timesheet_domain(self):
        try:
            current_day = date.today().strftime("%A")
            if current_day != 'Monday':
                yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()
            else:
                object_timesheet = self.env['account.analytic.line'].sudo().search([('create_date', '!=', date.today()), ('user_id', '=', self.env.user.id)], limit=1, order='create_date desc')
                print("\nDebug--------------------object_timesheet", object_timesheet)
                yesterday = object_timesheet.date
            print("\nDebug--------------------yesterday timesheet", yesterday)
            return [('date', '=', yesterday)]
        except Exception as e:
            print("\nDebug--------------------Error", e)


    editable_window = fields.Boolean(compute='_compute_editable_window', store=False)

    @api.depends_context('tz')
    def _compute_editable_window(self):
        for user in self:
            # Get current datetime in user timezone
            now_dt = fields.Datetime.context_timestamp(user, fields.Datetime.now())
            now_time = now_dt.time()
            # Define your window
            start_time = time(12, 0)
            end_time = time(20, 0)
            # Check if current time is in range
            user.editable_window = start_time <= now_time <= end_time