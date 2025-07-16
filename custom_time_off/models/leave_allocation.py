from odoo import models, fields, api
from datetime import datetime, timedelta

class QuarterlyLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    @api.model
    def quarterly_leave_allocation(self):
        employees = self.env['hr.employee'].search([('active', '=', True), ('name', '=', 'Web  Devloper1')])  # Fetch all employees
        current_date = datetime.now().date()

        # Determine the current quarter's start and end dates
        if current_date.month in [1, 2, 3]:
            quarter_start = datetime(current_date.year, 1, 1).date()
            quarter_end = datetime(current_date.year, 3, 31).date()
        elif current_date.month in [4, 5, 6]:
            quarter_start = datetime(current_date.year, 4, 1).date()
            quarter_end = datetime(current_date.year, 6, 30).date()
        elif current_date.month in [7, 8, 9]:
            quarter_start = datetime(current_date.year, 7, 1).date()
            quarter_end = datetime(current_date.year, 9, 30).date()
        else:  # October - December
            quarter_start = datetime(current_date.year, 10, 1).date()
            quarter_end = datetime(current_date.year, 12, 31).date()

        for employee in employees:
            # Check if allocation already exists for this quarter
            existing_paid_leave = self.env['hr.leave.allocation'].search([
                ('employee_id', '=', employee.id),
                ('name', '=', 'Quarterly Paid Leave Allocation'),
                ('create_date', '>=', quarter_start)
            ])

            print("\nDebug----------------------- existing_paid_leave ----------------------->", existing_paid_leave)

            existing_sick_leave = self.env['hr.leave.allocation'].search([
                ('employee_id', '=', employee.id),
                ('name', '=', 'Quarterly Sick Leave Allocation'),
                ('create_date', '>=', quarter_start)
            ])

            print("\nDebug----------------------- existing_paid_leave ----------------------->", existing_paid_leave)

            # Add Paid Leave if not already allocated
            if not existing_paid_leave:
                self.env['hr.leave.allocation'].create({
                    'name': 'Quarterly Paid Leave Allocation',
                    'employee_id': employee.id,
                    'holiday_status_id': self.env.ref('hr_holidays.holiday_status_cl').id,  # Paid Leave Type
                    'number_of_days': 3,
                    'state': 'confirm',
                    'date_from': quarter_start,
                })

            # Add Sick Leave if not already allocated
            if not existing_sick_leave:
                self.env['hr.leave.allocation'].create({
                    'name': 'Quarterly Sick Leave Allocation',
                    'employee_id': employee.id,
                    'holiday_status_id': self.env.ref('hr_holidays.holiday_status_sl').id,  # Sick Leave Type
                    'number_of_days': 1,
                    'state': 'confirm',
                    'date_from': quarter_start,
                    'date_to': quarter_end,  # Expire after the quarter
                })

        return True

    @api.model
    def yearly_leave_allocation(self):
        employees = self.env['hr.employee'].search([('active', '=', True), ('name', '=', 'Web  Devloper1')])  # Fetch all employees
        current_date = datetime.now().date()
        year_start = datetime(current_date.year, 1, 1).date()
        year_end = datetime(current_date.year, 12, 31).date()

        for employee in employees:
            # Check if allocation already exists for this year
            existing_festival_leave = self.env['hr.leave.allocation'].search([
                ('employee_id', '=', employee.id),
                ('name', '=', 'Yearly Festival Leave Allocation'),
                ('create_date', '>=', year_start)
            ])

            existing_birthday_anniversary_leave = self.env['hr.leave.allocation'].search([
                ('employee_id', '=', employee.id),
                ('name', '=', 'Yearly Birthday/Anniversary Leave Allocation'),
                ('create_date', '>=', year_start)
            ])

            # Add Festival Leave if not already allocated
            if not existing_festival_leave:
                self.env['hr.leave.allocation'].create({
                    'name': 'Yearly Festival Leave Allocation',
                    'employee_id': employee.id,
                    'holiday_status_id': self.env.ref('custom_time_off.holiday_status_festival').id,  # Festival Leave Type
                    'number_of_days': 1,
                    'state': 'confirm',
                    'date_from': year_start,
                    'date_to': year_end,
                })

            # Add Birthday/Anniversary Leave if not already allocated
            if not existing_birthday_anniversary_leave:
                self.env['hr.leave.allocation'].create({
                    'name': 'Yearly Birthday/Anniversary Leave Allocation',
                    'employee_id': employee.id,
                    'holiday_status_id': self.env.ref('custom_time_off.holiday_status_birthday').id,
                    # Birthday/Anniversary Leave Type
                    'number_of_days': 1,
                    'state': 'confirm',
                    'date_from': year_start,
                    'date_to': year_end,
                })

        return True

