from odoo import api, fields, models, tools
from datetime import datetime
from dateutil.relativedelta import relativedelta


class EmployeeAttendanceReport(models.Model):
    _name = 'employee.attendance.report'
    _description = 'Employee Attendance Report'
    _auto = False

    employee_id = fields.Many2one('hr.employee', string='Employee', readonly=True)
    # name = fields.Char('Name', readonly=True)
    date = fields.Date('Date', readonly=True)
    is_present = fields.Integer('Is Present', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW employee_attendance_report AS (
                SELECT 
                    row_number() OVER() AS id,
                    he.id AS employee_id,
                    gs.date AS date,
                    CASE 
                        WHEN ha.id IS NOT NULL THEN 1
                        ELSE 0
                    END AS is_present
                FROM
                    (
                        SELECT generate_series(
                            (SELECT MIN(check_in)::date FROM hr_attendance),
                            (SELECT MAX(check_in)::date FROM hr_attendance),
                            interval '1 day'
                        )::date AS date
                    ) AS gs
                CROSS JOIN hr_employee he
                LEFT JOIN hr_attendance ha 
                    ON ha.employee_id = he.id AND ha.check_in::date = gs.date
            )
        """)

    # def init(self):
    #     tools.drop_view_if_exists(self.env.cr, self._table)
        
    #     # Get today's date and the first day of the current month
    #     today = fields.Date.today()
    #     first_day_of_month = today.replace(day=1)
    #     last_day_of_month = (first_day_of_month + relativedelta(months=1, days=-1))
        
    #     # SQL query to generate the attendance data for the current month
    #     self.env.cr.execute("""
    #         CREATE OR REPLACE VIEW employee_attendance_report AS (
    #             SELECT 
    #                 row_number() OVER() AS id,
    #                 he.id AS employee_id,
    #                 gs.date AS date,
    #                 CASE 
    #                     WHEN ha.id IS NOT NULL THEN 1
    #                     ELSE 0
    #                 END AS is_present
    #             FROM
    #                 (
    #                     SELECT generate_series(
    #                         %s::date,
    #                         %s::date,
    #                         interval '1 day'
    #                     )::date AS date
    #                 ) AS gs
    #             CROSS JOIN hr_employee he
    #             LEFT JOIN hr_attendance ha 
    #                 ON ha.employee_id = he.id AND ha.check_in::date = gs.date
    #             WHERE gs.date >= %s AND gs.date <= %s
    #         )
    #     """, (first_day_of_month, last_day_of_month, first_day_of_month, last_day_of_month))




