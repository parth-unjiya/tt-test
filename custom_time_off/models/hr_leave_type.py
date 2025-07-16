from datetime import date, timedelta
from odoo import models, fields


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    allocation_type = fields.Selection([
        ('manual', 'Manual'),
        ('automate', 'Automate')
    ], string='Leave Allocation Type', default='manual')

    allocation_frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly')
    ], string='Allocation Frequency')

    allocation_date = fields.Date(string='Allocation Date')

    leave_amount = fields.Float(string='Leave Amount')

    leave_validity_period = fields.Selection([
        ('monthly_end', 'Until End of Month'),
        ('quarterly_end', 'Until End of Quarter'),
        ('yearly_end', 'Until End of Year'),
        ('custom_days', 'Custom Number of Days'),
    ], string="Leave Validity Period", default="yearly_end")

    leave_validity_days = fields.Integer(string='Custom Validity Days')

    allowed_employment_status = fields.Selection([
        ('all', 'All Employees'),
        ('permanent_only', 'Permanent Employees Only'),
    ], string="Allowed For", default='permanent_only')

    def _auto_allocate_leaves(self):
        today = fields.Date.today()
        leave_types = self.search([
            ('allocation_type', '=', 'automate'),
            ('allocation_date', '<=', today),
            ('leave_amount', '>', 0),
        ])

        print("\n\nDEBUG: ======= Leave Type: =======\n", leave_types)

        for leave_type in leave_types:
            if not leave_type._is_allocation_day(today):
                continue

            start_date, end_date = leave_type._get_allocation_period(today)
            
            print("\n\nDEBUG: start_date: ", start_date)
            print("DEBUG: end_date: ", end_date, "\n\n")

             # Adjust employee filtering based on leave type rule
            if leave_type.allowed_employment_status == 'all':
                # all employees
                employees = self.env['hr.employee'].search([
                    ('active', '=', True),
                ])
            else:
                # Only permanent employees
                employees = self.env['hr.employee'].search([
                    ('active', '=', True),
                    ('status', '=', 'permanent')
                ])
            
            print("\n\nDEBUG: employees len: ", len(employees))

            for emp in employees:

                # ✅ Check based on create_date, not request_date_from/to
                existing_allocation = self.env['hr.leave.allocation'].search_count([
                    ('employee_id', '=', emp.id),
                    ('holiday_status_id', '=', leave_type.id),
                    ('create_date', '>=', fields.Datetime.to_datetime(start_date)),
                    ('create_date', '<=', fields.Datetime.to_datetime(end_date)),
                ])
                if existing_allocation:
                    print("DEBUG: # Already allocated during this period")
                    continue  # Already allocated during this period

                # Use today's date range for request fields
                request_date_from = today
                request_date_to = leave_type._get_expiry_date(today)

                print("\n\nDEBUG: request_date_from: ", request_date_from)
                print("DEBUG: request_date_to: ", request_date_to)

                leave_allocation = self.env['hr.leave.allocation'].create({
                    'name': f'Auto Allocation - {leave_type.name}',
                    'holiday_status_id': leave_type.id,
                    'employee_id': emp.id,
                    'number_of_days': leave_type.leave_amount,
                    'mode_company_id': emp.company_id.id,
                    'date_from': request_date_from,
                    'date_to': request_date_to,
                })
                leave_allocation.action_validate()

    def _is_allocation_day(self, today):
        """Check if allocation should run today based on frequency."""
        if self.allocation_frequency == 'monthly':
            print("\n\nDEBUG: Call monthly: ", today)
            return today.day == self.allocation_date.day
        elif self.allocation_frequency == 'quarterly':
            # Quarterly: Jan, Apr, Jul, Oct
            print("\n\nDEBUG: Call quarterly: ", today, today.month)
            print("\n\nDEBUG: condition: ", today.day == self.allocation_date.day and today.month in [1, 4, 7, 10])
            return today.day == self.allocation_date.day and today.month in [1, 4, 7, 10]
        elif self.allocation_frequency == 'yearly':
            print("\n\nDEBUG: Call yearly: ", today)
            return today.day == self.allocation_date.day and today.month == self.allocation_date.month
        return False


    def _get_expiry_date(self, from_date):
        if self.leave_validity_period == 'monthly_end':
            next_month = (from_date.replace(day=1) + timedelta(days=32)).replace(day=1)
            return next_month - timedelta(days=1)
        elif self.leave_validity_period == 'quarterly_end':
            quarter = (from_date.month - 1) // 3 + 1
            end_month = quarter * 3
            year = from_date.year
            next_quarter = (end_month % 12) + 1
            next_quarter_year = year if end_month < 12 else year + 1
            return date(next_quarter_year, next_quarter, 1) - timedelta(days=1)
        elif self.leave_validity_period == 'yearly_end':
            return date(from_date.year, 12, 31)
        elif self.leave_validity_period == 'custom_days' and self.leave_validity_days:
            return from_date + timedelta(days=self.leave_validity_days)
        return from_date


    def _get_allocation_period(self, today):
        if self.allocation_frequency == 'monthly':
            start = today.replace(day=1)
            next_month = (start + timedelta(days=32)).replace(day=1)
            end = next_month - timedelta(days=1)
        elif self.allocation_frequency == 'quarterly':
            quarter = (today.month - 1) // 3 + 1
            start_month = (quarter - 1) * 3 + 1
            start = date(today.year, start_month, 1)
            if start_month + 3 > 12:
                end = date(today.year, 12, 31)
            else:
                end = date(today.year, start_month + 3, 1) - timedelta(days=1)
        elif self.allocation_frequency == 'yearly':
            start = date(today.year, 1, 1)
            end = date(today.year, 12, 31)
        else:
            start = end = today
        return start, end