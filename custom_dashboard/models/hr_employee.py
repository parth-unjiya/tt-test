# -*- coding: utf-8 -*-

from collections import defaultdict
from datetime import timedelta, datetime, date
from dateutil.relativedelta import relativedelta
from odoo.tools import float_round

from odoo import api, fields, models, _


def decimal_to_hhmmss(decimal_hours):
    total_seconds = int(decimal_hours * 3600)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class HrEmployee(models.Model):
    """Inherit hr.employee to add birthday field and custom methods."""

    _inherit = "hr.employee"

    @api.model
    def get_user_employee_details(self):
        user = self.env.user
        employee = self.sudo().search([("user_id", "=", user.id)], limit=1)
        return (
            employee.read(["id", "user_id", "job_id", "country_id", "mobile_phone", "gender", "name", "image_1920", "birthday", "joining_date"])
            if employee
            else {}
        )

    @api.model
    def get_employee_other_details(self, filter_type):
        # Get logged-in user
        user = self.env.user
        employee = self.search([("user_id", "=", user.id)], limit=1)

        # Determine date filters
        today = fields.Date.today()
        start_of_week = today - timedelta(days=today.weekday())  # Monday of this week
        start_of_month = today.replace(day=1)  # First day of this month
        start_of_year = today.replace(month=1, day=1)  # First day of this year

        date = False

        if filter_type == 'this_day':
            date = today
        elif filter_type == 'this_week':
            date = start_of_week
        elif filter_type == 'this_month':
            date = start_of_month
        elif filter_type == 'this_year':
            date = start_of_year

        # Filter Timesheets by the date range
        timesheet_count = (
            self.env["account.analytic.line"]
            .sudo()
            .search_count([
                ("project_id", "!=", False), 
                ("user_id", "=", user.id), 
                ("date", ">=", date)
            ])
        )
        print("timesheet_count", timesheet_count)
        # Filter Leave Requests by the date range
        leave_requests_count = (
            self.env['hr.leave']
            .sudo()
            .search_count([('state', 'in', ['confirm', 'validate1']), ('create_date', '>=', date)])
        )

        # Filter Job Applications by the date range
        job_application_count = (
            self.env['hr.applicant']
            .sudo()
            .search_count([("user_id", "=", user.id), ("create_date", ">=", date)])
        )

        # Count Payslips (assuming payslips are filtered by the payslip period)
        # payslip_count = len(employee.slip_ids.sudo().filtered(lambda s: s.create_date >= date))

        # Create the result data
        if employee:
            data = {
                "timesheet_count": timesheet_count,
                "leave_requests_count": leave_requests_count,
                # "payslip_count": payslip_count,
                "job_application_count": job_application_count,
            }

        return data

    @api.model
    def get_user_projects_summary(self, stage):
        print("---------------> stage", stage)
        # Get the logged-in user
        current_user = self.env.user

        # Fetch projects where the user is either the project manager or is assigned to at least one task
        user_projects = self.env['project.project'].sudo().search([
            '|',
            ('user_id', '=', current_user.id),  # Project manager
            ('task_ids.user_ids', 'in', [current_user.id]), # Assigned to any task
            ('stage_id.sequence', '=', int(stage)) if stage != 'all' else ('stage_id', '!=', False),
            ('active', '=', True)
        ])
        
        project_data = []

        for project in user_projects:
            # Get all tasks count
            total_tasks = len(project.task_ids)
            # Calculate total hours spent on these tasks
            total_hours_spent = sum(task.total_hours_spent for task in project.task_ids)
            # Calculate total allocated_hours on these tasks
            allocated_hours = project.allocated_hours

            # Append the project data
            project_data.append({
                'id': project.id,
                'project_name': project.name,
                'allocated_hours': decimal_to_hhmmss(allocated_hours) if allocated_hours else "00:00:00",
                'total_hours_spent': decimal_to_hhmmss(total_hours_spent) if total_hours_spent else "00:00:00",
                'total_tasks': total_tasks,
            })
        print("=========================>project_data", project_data)
        # Return the summarized data
        return project_data
    
    @api.model
    def get_user_task_summary(self, filter_type, month_data):
        """
        Fetch tasks assigned to the logged-in user and filter them based on the date assigned.
        
        :param filter_type: Filter to apply ('this_day', 'this_week', 'this_month')
        :return: List of tasks with their project name, status, and time details
        """
        # Get the logged-in user
        current_user = self.env.user
        today = fields.Date.today()
        
        # Determine the date range based on the filter_type
        if filter_type == 'this_day':
            start_date = today
            end_date = today + timedelta(days=1)
        
        elif filter_type == 'this_week':
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=7)
        
        elif filter_type == 'this_month':
            start_date = today.replace(day=1)
            end_date = (start_date + relativedelta(months=1)) - timedelta(days=1)

        elif filter_type == 'custom_month':
            if month_data:
                # Assume 'month' is a string in format 'YYYY-MM'
                start_date = datetime.strptime(month_data, '%Y-%m').date()
                end_date = (start_date + relativedelta(months=1)) - timedelta(days=1)
            else:
                raise ValueError("Month parameter is required for 'custom_month' filter_type.")
        
        else:
            raise ValueError("Invalid filter_type. Must be 'this_day', 'this_week', or 'this_month'.")

        # Fetch tasks assigned to the user within the date range
        user_tasks = self.env['project.task'].sudo().search([
            ('user_ids', 'in', [current_user.id]),
            ('date_assign', '>=', start_date),
            ('date_assign', '<', end_date),
            ('active', '=', True)
        ])
        
        task_data = []
        
        for task in user_tasks:
            # Get the project associated with the task
            project_name = task.project_id.name if task.project_id else 'No Project'
            
            # Append the task data
            task_data.append({
                'id': task.id,
                'project_name': project_name,
                'task_name': task.name,
                'date_assign': task.date_assign if task.date_assign else None,  
                'date_deadline': task.date_deadline if task.date_deadline else None,
                'total_hours_spent': decimal_to_hhmmss(task.total_hours_spent) or "00:00:00",
                'status': task.stage_id.name if task.stage_id else 'No Stage'
            })
        
        return task_data
    
    @api.model
    def get_project_stage(self):
        stage_obj = self.env['project.project.stage'].sudo().search([])
        stage = []
        # Collect name and sequence for each stage
        for stage_record in stage_obj:
            stage.append({
                'id': stage_record.id,
                'name': stage_record.name,
                'sequence': stage_record.sequence,
            })
        return stage

    @api.model
    def get_department(self):
        department_obj = self.env['hr.department'].sudo().search([])
        department = []
        # Collect name and sequence for each stage
        for department_record in department_obj:
            department.append({
                'id': department_record.id,
                'name': department_record.name,
            })
        return department
    
    # @api.model
    # def get_tasks_stage(self):
    #     stage_obj = self.env['project.task.type'].search([])
    #     stage = []
    #     # Collect name and sequence for each stage
    #     for stage_record in stage_obj:
    #         stage.append({
    #             'name': stage_record.name,
    #             'sequence': stage_record.sequence,
    #         })
    #     print("=============>", stage)
    #     return stage
    
    @api.model
    def get_employee_leave_request(self, filter_type, month_data):
        
        user = self.env.user
        today = fields.Date.today()

        # Filter by the requested period
        if filter_type == "this_day":
            # Get today's date
            start_date = today
            end_date = today + timedelta(days=1)

        elif filter_type == "this_week":
            # Get the start and end of the current week
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=7)

        elif filter_type == "this_month":
            # Get the start and end of the current month
            start_date = today.replace(day=1)
            end_date = (start_date + relativedelta(months=1)) - timedelta(days=1)

        elif filter_type == 'custom_month':
            if month_data:
                # Assume 'month' is a string in format 'YYYY-MM'
                start_date = datetime.strptime(month_data, '%Y-%m').date()
                end_date = (start_date + relativedelta(months=1)) - timedelta(days=1)
            else:
                raise ValueError("Month parameter is required for 'custom_month' filter_type.")

        else:
            raise ValueError("Invalid filter_type. Must be 'this_day', 'this_week', or 'this_month'.")


        # employee_list = self.search([('leave_manager_id', '=', user.id)])

        leave_requests = self.env['hr.leave'].sudo().search([
            ('request_date_from', '>=', start_date),
            ('request_date_to', '<=', end_date)
        ])
        
        emp_leave_data = []
        for leave in leave_requests:
            emp_leave_data.append({
                'id': leave.id,
                'name': leave.employee_id.name,
                'type': leave.holiday_status_id.name,
                'leave_day': leave.number_of_days,
                'from_date': leave.request_date_from.strftime('%d-%m-%Y'),
                'to_date': leave.request_date_to.strftime('%d-%m-%Y'),
            })

        return emp_leave_data

    @api.model
    def get_employee_timesheet(self, filter_type, user_id, month_data):
        print("\n\n================= get_employee_timesheet START =================\n\n")
        print("filter_type", filter_type)
        print("\nemployee_id", user_id)
        print("\nmonth_data", month_data)
        today = fields.Date.today()

        # Filter by the requested period
        if filter_type == "this_day":
            # Get today's date
            start_date = today
            end_date = today + timedelta(days=1)

        elif filter_type == "this_week":
            # Get the start and end of the current week
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=7)

        elif filter_type == "this_month":
            # Get the start and end of the current month
            start_date = today.replace(day=1)
            end_date = (start_date + relativedelta(months=1)) - timedelta(days=1)

        elif filter_type == 'custom_month':
            if month_data:
                # Assume 'month' is a string in format 'YYYY-MM'
                start_date = datetime.strptime(month_data, '%Y-%m').date()
                end_date = (start_date + relativedelta(months=1)) - timedelta(days=1)
            else:
                raise ValueError("Month parameter is required for 'custom_month' filter_type.")

        else:
            raise ValueError("Invalid filter_type. Must be 'this_day', 'this_week', or 'this_month'.")

        if user_id:
            timesheet_requests = self.env['hr.attendance'].sudo().search([
                ('employee_id', '=', int(user_id)),
                ('check_in', '>=', start_date),
                ('check_in', '<', end_date)
            ])
            print("timesheet_requests", timesheet_requests)
        else:
            timesheet_requests = self.env['hr.attendance'].sudo().search([
                ('check_in', '>=', start_date),
                ('check_in', '<', end_date)
            ])

        timesheet_data = []
        for timesheet in timesheet_requests:
            timesheet_data.append({
                'id': timesheet.id,
                'name': timesheet.employee_id.name,
                'create_date': timesheet.create_date.strftime('%d-%m-%Y'),
                'check_in': timesheet.check_in if timesheet.check_in else "00:00:00",
                'check_out': timesheet.check_out if timesheet.check_out else '00:00:00',
                'worked_hours': '{:02d}:{:02d}'.format(int(timesheet.worked_hours), int(round((timesheet.worked_hours % 1) * 60))),
                'lunch_time': decimal_to_hhmmss(timesheet.lunch_time) if timesheet.lunch_time else '00:00:00',
                'break_time': decimal_to_hhmmss(timesheet.break_time) if timesheet.break_time else '00:00:00',
                'estimate_time': decimal_to_hhmmss(timesheet.estimate_time) if timesheet.estimate_time else '00:00:00',
                'floor_active_time': decimal_to_hhmmss(timesheet.floor_active_time) if timesheet.floor_active_time else '00:00:00',
                'general_meeting_time': decimal_to_hhmmss(timesheet.general_meeting_time) if timesheet.general_meeting_time else '00:00:00',
                'interview_time': decimal_to_hhmmss(timesheet.interview_time) if timesheet.interview_time else '00:00:00',
                'no_work_time': decimal_to_hhmmss(timesheet.no_work_time) if timesheet.no_work_time else '00:00:00',
                'r_and_d_time': decimal_to_hhmmss(timesheet.r_and_d_time) if timesheet.r_and_d_time else '00:00:00',
            })
        print("\n\n================= get_employee_timesheet END =================\n\n")
        return timesheet_data



    @api.model
    def get_manager_leave_request(self, filter_type, month_data):
        
        user = self.env.user
        today = fields.Date.today()

        # Filter by the requested period
        if filter_type == "this_day":
            # Get today's date
            start_date = today
            end_date = today + timedelta(days=1)

        elif filter_type == "this_week":
            # Get the start and end of the current week
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=7)

        elif filter_type == "this_month":
            # Get the start and end of the current month
            start_date = today.replace(day=1)
            end_date = (start_date + relativedelta(months=1)) - timedelta(days=1)

        elif filter_type == 'custom_month':
            if month_data:
                # Assume 'month' is a string in format 'YYYY-MM'
                start_date = datetime.strptime(month_data, '%Y-%m').date()
                end_date = (start_date + relativedelta(months=1)) - timedelta(days=1)
            else:
                raise ValueError("Month parameter is required for 'custom_month' filter_type.")

        else:
            raise ValueError("Invalid filter_type. Must be 'this_day', 'this_week', or 'this_month'.")


        employee_list = self.sudo().search([('leave_manager_id', '=', user.id)])

        emp_leave_data = []
        if employee_list:
            for emp in employee_list:
                leave_requests = self.env['hr.leave'].sudo().search([
                    ('employee_id', '=', emp.id), 
                    ('state', '=', 'confirm'),
                    ('request_date_from', '>=', start_date),
                    ('request_date_to', '<=', end_date)
                ])
                # Collect Leave Request data
                for leave in leave_requests:
                    emp_leave_data.append({
                        'id': leave.id,
                        'name': leave.employee_id.name,
                        'type': leave.holiday_status_id.name,
                        'leave_day': leave.number_of_days,
                        'from_date': leave.request_date_from,
                        'to_date': leave.request_date_to,
                    })
        return emp_leave_data
    
    @api.model
    def get_attendance_data(self, filter_type, month_data):
        """
        Get attendance data for the logged-in user based on the filter type.
        
        :param filter_type: Type of filter to apply ('this_day', 'this_week', 'this_month')
        :return: List of attendance data with 'check_in', 'check_out', and 'worked_hours'
        """
        current_user = self.env.user
        print("Debug=======================-----current_user", current_user, month_data, filter_type)
        today = fields.Date.today()

        # Filter by the requested period
        if filter_type == "this_day":
            # Get today's date
            start_date = today
            end_date = today + timedelta(days=1)

        elif filter_type == "this_week":
            # Get the start and end of the current week
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=7)

        elif filter_type == "this_month":
            # Get the start and end of the current month
            start_date = today.replace(day=1)
            end_date = (start_date + relativedelta(months=1)) - timedelta(days=1)

        elif filter_type == 'custom_month':
            if month_data:
                # Assume 'month' is a string in format 'YYYY-MM'
                start_date = datetime.strptime(month_data, '%Y-%m').date()
                end_date = (start_date + relativedelta(months=1)) - timedelta(days=1)
            else:
                raise ValueError("Month parameter is required for 'custom_month' filter_type.")

        else:
            raise ValueError("Invalid filter_type. Must be 'this_day', 'this_week', or 'this_month'.")

        print("\nDebug=============================----filter_type----", filter_type, start_date, end_date)

        # Fetch attendance records for the current user
        attendances = self.env['hr.attendance'].sudo().search([
            ('employee_id.user_id', '=', current_user.id),
            ('check_in', '>=', start_date),
            ('check_in', '<', end_date)
        ])

        # Prepare the attendance data
        attendance_data = []
        for attendance in attendances:
            
            attendance_data.append({
                'id': attendance.id,
                'check_in': attendance.check_in if attendance.check_in else "00:00:00",
                'check_out': attendance.check_out if attendance.check_out else '00:00:00',
                'worked_hours': '{:02d}:{:02d}'.format(int(attendance.worked_hours), int(round((attendance.worked_hours % 1) * 60)))
            })
        print("\nDebug=============================----attendance_data----", attendance_data)
        return attendance_data

    @api.model
    def get_birthdays_today(self):
        # Get today's date
        today = datetime.now().date()
        
        # Extract month and day from today's date
        current_month = today.month
        current_day = today.day
        
        # Search for employees whose birthday is not null
        birthday_employees = self.sudo().search([
            ('birthday', '!=', False),  # Ensure birthday is set
        ])
        
        # Filter employees based on today's month and day
        today_birthdays = [
            employee for employee in birthday_employees 
            if employee.birthday.month == current_month and employee.birthday.day == current_day
        ]

        # Prepare the list of dictionaries
        employee_data = []
        for employee in today_birthdays:
            employee_data.append({
                'id': employee.id,
                'name': employee.name,
                'email': employee.work_email or 'No email',
                'department': employee.department_id.name if employee.department_id else 'No department',
                'birthday': employee.birthday.strftime('%d-%m-%Y') if employee.birthday else 'No birthday',
            })
        
        return employee_data

    @api.model
    def get_candidate_interview_data(self):
        
        # Fetch candidate interview records
        interview_obj = self.env['hr.applicant'].sudo().search([
            ('date_closed', '=', False), 
            ('active', '=', True), 
            ('refuse_reason_id', '=', False)
        ])

        # Prepare the interview data
        interview_data = []
        for interview in interview_obj:
            
            interview_data.append({
                'id': interview.id,
                'name': interview.partner_name,
                'email': interview.email_from,
                'availability': interview.availability.strftime('%d-%m-%Y') if interview.availability else 'Not Set',
                'stage': interview.stage_id.name if interview.stage_id else 'Empty'
            })

        return interview_data

    @api.model
    def get_employee_data(self, department_id=None):
        """
        Fetch employee data based on the department.
        
        If department_id is provided, return employees in that department.
        Otherwise, return all employees.
        """
        print("==================== department_id", department_id)
        print("==================== department_id", type(department_id))

        domain = []
        if department_id:
            domain = [('department_id', '=', int(department_id))]
        
        # Fetch employee records based on the domain
        employee_obj = self.sudo().search(domain)

        # Prepare data to return
        employee_data = []
        for employee in employee_obj:
            employee_data.append({
                'id': employee.id,
                'name': employee.name,
                # 'email': employee.work_email,
                # 'department': employee.department_id.name if employee.department_id else "N/A",
                # 'date_of_birth': employee.birthday,
                # 'joining_date': employee.joining_date,
            })
        
        return employee_data

    @api.model
    def get_project_milestone(self):
    
        # Get the logged-in user
        current_user = self.env.user

        # Fetch projects where the user is either the project manager or is assigned to at least one task
        user_projects = self.env['project.project'].sudo().search([
            ('user_id', '=', current_user.id),  # Project manager
            ('active', '=', True)
        ])
        
        project_data = []

        for project in user_projects:
            # Append the project data
            project_data.append({
                'id': project.id,
                'project_name': project.name,
                'project_manager': project.user_id.name,
                'project_amount': 1100,
                'milestone_amount': 2100,
                'milestone_start_date': project.date_start,

            })
        print("\n=================>get_project_milestone", project_data)
        # Return the summarized data
        return project_data

    @api.model
    def get_top_projects_by_timesheet(self):
        # Top 10 Project Highly Consume Hours
        # Query to get total timesheet hours per project
        
        query = """
            SELECT project_id, SUM(unit_amount) as total_hours
            FROM account_analytic_line
            WHERE project_id IS NOT NULL
            GROUP BY project_id
            ORDER BY total_hours DESC
            LIMIT 10
        """
        self.env.cr.execute(query)
        project_hours = self.env.cr.fetchall()  # List of tuples (project_id, total_hours)

        project_data = []
        project_model = self.env['project.project'].sudo()

        for project_id, total_hours in project_hours:
            project = project_model.browse(project_id)
            project_data.append({
                'id': project.id,
                'project_name': project.name,
                'project_manager': project.user_id.name,
                'total_hours': decimal_to_hhmmss(total_hours),  # Total logged hours
            })
        return project_data

    # @api.model
    # def get_absentees_details(self):
    #     today = date.today()
        
    #     first_day_of_month = today.replace(day=1)

    #     # Get all active employees
    #     all_employees = self.env['hr.employee'].sudo().search([('active', '=', True)])


    #     # Query for employees who are on leave today
    #     leave_records = self.env['hr.leave'].sudo().search([
    #         ('state', '=', 'validate'),  # Approved leaves only
    #         ('date_from', '<=', today),  # Leave started before or on today
    #         ('date_to', '>=', today)     # Leave ends on or after today
    #     ])

    #     absentees_list = []
    #     sr_no = 1
    #     print("\n********leave_records*********", leave_records)
    #     for leave in leave_records:
    #         employee = leave.employee_id

    #         # Count leaves in the current month
    #         total_leaves_this_month = self.env['hr.leave'].sudo().search_count([
    #             ('employee_id', '=', employee.id),
    #             ('state', '=', 'validate'),
    #             ('date_from', '>=', first_day_of_month),
    #             ('date_to', '<=', today)
    #         ])

    #         # Append formatted data
    #         absentees_list.append({
    #             'id': leave.id,
    #             'sr_no': sr_no,  
    #             'emp_code': employee.barcode,  # Employee Code
    #             'name': employee.name,
    #             'department': employee.department_id.name or "N/A",
    #             'company': employee.company_id.name or "N/A",
    #             'leave_today': True,  # Boolean for better usability
    #             'leave_current_month': total_leaves_this_month,
    #             'is_informed': True if leave.state == 'validate' else False,  # Boolean for informed leave
    #             'till_date': leave.date_to.strftime('%Y-%m-%d')
    #         })
    #         sr_no += 1

    #     print("\n\n=========================> Absentees Data", absentees_list)
    #     return absentees_list

    @api.model
    def get_absentees_details(self):
        today = date.today()
        first_day_of_month = today.replace(day=1)

        # Get all active employees in a single query
        all_employees = self.env['hr.employee'].sudo().search_read(
            [('active', '=', True)],
            ['id', 'emp_code', 'name', 'department_id', 'company_id']
        )

        # Get employees who have an approved leave today
        leave_employees = set(self.env['hr.leave'].sudo().search([
            ('state', '=', 'validate'),
            ('date_from', '<=', today),
            ('date_to', '>=', today)
        ]).mapped('employee_id.id'))  # Convert to a set for faster lookup

        # Get employees who have attended today
        attended_employees = set(self.env['hr.attendance'].sudo().search([
            ('check_in', '>=', today.strftime('%Y-%m-%d 00:00:00')),
            ('check_in', '<=', today.strftime('%Y-%m-%d 23:59:59'))
        ]).mapped('employee_id.id'))  # Convert to a set for faster lookup

        absentees_list = []
        sr_no = 1

        for employee in all_employees:
            emp_id = employee['id']

            # Check if employee is absent (not on leave and not attended)
            if emp_id not in leave_employees and emp_id not in attended_employees:

                # Count leaves in the current month (Optimized Query)
                total_leaves_this_month = self.env['hr.leave'].sudo().search_count([
                    ('employee_id', '=', emp_id),
                    ('state', '=', 'validate'),
                    ('date_from', '>=', first_day_of_month),
                    ('date_to', '<=', today)
                ])

                absentees_list.append({
                    'id': emp_id,
                    'sr_no': sr_no,
                    'emp_code': employee.get('emp_code', "N/A"),  # Employee Code
                    'name': employee.get('name', "N/A"),
                    'department': self.env['hr.department'].browse(employee.get('department_id')[0]).name if employee.get('department_id') else "N/A",
                    'company': self.env['res.company'].browse(employee.get('company_id')[0]).name if employee.get('company_id') else "N/A",
                    'is_absent': True,  # Marked as absent
                    'leave_applied': False,  # No leave applied
                    'leave_current_month': total_leaves_this_month,
                    'attendance_recorded': False,  # No attendance
                    'absence_date': today.strftime('%d-%m-%Y'),
                })
                sr_no += 1

        # print("=========================> Absentees Without Leave", absentees_list)
        return absentees_list

    @api.model
    def get_employee_total_activity_time(self, employee_id, start_date, end_date):
        """Return total hours for key activity types within the date range for a given employee."""
        print("\n=================>get_employee_total_activity_time", employee_id, start_date, end_date)

        # Ensure datetime format (if passed as strings)
        if isinstance(start_date, str):
            start_date = fields.Datetime.from_string(start_date)
        if isinstance(end_date, str):
            end_date = fields.Datetime.from_string(end_date)

        print("\n=================>get_employee_total_activity_time", start_date, end_date)

        # Search attendance records
        attendances = self.env['hr.attendance'].search([
            ('employee_id', '=', int(employee_id)),
            ('check_in', '>=', start_date),
            ('check_out', '<=', end_date),
        ])

        print("\n=================>get_employee_total_activity_time", attendances)
        # Initialize totals
        totals = {
            'interview_time': 0.0,
            'estimate_time': 0.0,
            'floor_active_time': 0.0,
            'general_meeting_time': 0.0,
            'no_work_time': 0.0,
            'r_and_d_time': 0.0,
        }

        # Sum up times
        for rec in attendances:
            totals['interview_time'] += rec.interview_time or 0.0
            totals['estimate_time'] += rec.estimate_time or 0.0
            totals['floor_active_time'] += rec.floor_active_time or 0.0
            totals['general_meeting_time'] += rec.general_meeting_time or 0.0
            totals['no_work_time'] += rec.no_work_time or 0.0
            totals['r_and_d_time'] += rec.r_and_d_time or 0.0

        for key in totals:
            totals[key] = decimal_to_hhmmss(totals[key])

        print("\n=================>get_employee_total_activity_time", totals)
        return totals