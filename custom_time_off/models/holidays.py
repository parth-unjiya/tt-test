from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

from datetime import timedelta
from dateutil.relativedelta import relativedelta


class CustomHolidays(models.Model):
    _inherit = "hr.leave"

    tt_id = fields.Char(string="TT ID")

    contains_sandwich_leaves = fields.Boolean(
        string="Contains Sandwich Leaves",
    )

    dynamic_max_date = fields.Date(
        compute='_compute_dynamic_max_date', store=True
    )

    def _compute_dynamic_max_date(self):
        for rec in self:
            rec.dynamic_max_date = fields.Date.today() + relativedelta(days=60)

    @api.model_create_multi
    def create(self, vals):
        result = super(CustomHolidays, self).create(vals)
        for val in result:
            public_holidays = val.env["resource.calendar.leaves"].search(
                [("resource_id", "=", False)]
            )
            mandatory_holidays = val.env["hr.leave.mandatory.day"].search([])
            print("----------data----", mandatory_holidays, public_holidays)
            date_list = []
            if public_holidays:
                for public in public_holidays:
                    start_date = public.date_from + relativedelta(hours=5, minutes=30)
                    end_date = public.date_to + relativedelta(hours=5, minutes=30)
                    delta = end_date.date() - start_date.date()
                    print("----------delta----", delta, start_date, end_date)
                    date_list.extend(
                        (start_date + timedelta(days=i)).date()
                        for i in range(delta.days + 1)
                    )
            if mandatory_holidays:
                for mandatory in mandatory_holidays:
                    start_date = mandatory.start_date + relativedelta(hours=5, minutes=30)
                    end_date = mandatory.end_date + relativedelta(hours=5, minutes=30)
                    delta = end_date.date() - start_date.date()
                    print("----------delta----", delta, start_date, end_date)
                    date_list.extend(
                        (start_date + timedelta(days=i)).date()
                        for i in range(delta.days + 1)
                    )
            print("----------date_list----", date_list)

            if val.employee_id and val.employee_id.status == "probation":
                if result.holiday_status_id != val.env.ref(
                    "hr_holidays.holiday_status_unpaid"
                ):
                    raise ValidationError(
                        _("You can't apply for leave in probation period")
                    )


        return result

    # if result.holiday_status_id == self.env.ref(
    #     "custom_time_off.holiday_status_wfh"
    # ) and result.holiday_status_id.name in [
    #     "Work From Home",
    #     "work from home",
    #     "WFH",
    #     "wfh",
    # ]:
    #     if result.number_of_days_display and result.number_of_days_display < 5:
    #         raise warnings(
    #             _("You can't apply for Work From Home for less than 5 days")
    #         )


    # @api.depends(
    #     "request_date_from", "request_date_to", "holiday_status_id", "employee_id"
    # )
    # def _compute_contains_sandwich_leaves(self):
    #     for leave in self:
    #         rule = self.env["hr.sandwich.leave.rule"].search(
    #             [("leave_type_id", "=", leave.holiday_status_id.id)], limit=1
    #         )
    #         print("\n\nDEBUG: _compute_contains_sandwich_leaves", bool(rule))
    #         leave.contains_sandwich_leaves = bool(rule)

    def _apply_sandwich_rule(self, public_holidays, employee_leaves, days):
        """Apply the sandwich leave rule based on weekends, public holidays, and continuous leave."""
        self.ensure_one()
        if not self.request_date_from or not self.request_date_to:
            return self.number_of_days

        rule = self.env["hr.sandwich.leave.rule"].search(
            [("leave_type_id", "=", self.holiday_status_id.id)], limit=1
        )

        if not rule:
            return self.number_of_days  # No sandwich rule, return default count

        date_from = self.request_date_from
        date_to = self.request_date_to
        total_leaves = days
        # total_leaves = (date_to - date_from).days + 1

        today = fields.Date.today()
        notice_period = (date_from - today).days

        print("DEBUG: Checking Sandwich Rule Conditions")
        print(
            f" - Notice Period: {notice_period} (Min Required: {rule.notice_period_days})"
        )
        print(f" - Include Weekends: {rule.include_weekends}")
        print(f" - Include Public Holidays: {rule.include_public_holidays}")

        # **🔹 Skip sandwich rule if notice period is met**
        if notice_period >= rule.notice_period_days:
            print("DEBUG: Notice period met, skipping sandwich rule.")
            return total_leaves

        # **🔹 Skip sandwich rule if BOTH weekends & public holidays are excluded**
        if not rule.include_weekends and not rule.include_public_holidays:
            print(
                "DEBUG: Weekends & Public Holidays are excluded, skipping sandwich rule."
            )
            return total_leaves

        def is_non_working_day(date):
            """Checks if the given date is a weekend or a public holiday."""
            is_weekend = rule.include_weekends and date.weekday() in (5, 6)
            is_holiday = rule.include_public_holidays and date in public_holidays
            return is_weekend or is_holiday

        def count_sandwich_days(start_date, end_date, direction):
            """Counts additional leave days if surrounded by non-working days."""
            current_date = start_date + timedelta(days=direction)
            days_count = 0
            found_non_working_day = False  # Track if we find a weekend/holiday

            while start_date <= current_date <= end_date:  # Limit to leave range
                print("DEBUG: current_date: ", current_date)

                is_weekend = rule.include_weekends and current_date.weekday() in (5, 6)
                is_holiday = (
                    rule.include_public_holidays and current_date in public_holidays
                )

                if is_weekend or is_holiday:
                    days_count += 1
                    found_non_working_day = True
                else:
                    # If we already counted non-working days and now find a working day, stop
                    if found_non_working_day:
                        break

                current_date += timedelta(days=direction)

            print(f"DEBUG: days_count: {days_count}")
            return days_count

        total_leaves += count_sandwich_days(
            date_from, date_to, -1
        ) + count_sandwich_days(date_from, date_to, 1)

        print(f"DEBUG: Final Leave Days after Sandwich Rule: {total_leaves}")
        return total_leaves

    def _get_duration(self, check_leave_type=True, resource_calendar=None):
        print("\n\n\nDEBUG: _get_durations")
        result = super()._get_duration(check_leave_type, resource_calendar)
        public_holidays = self._get_public_holidays()

        leaves_by_employee = dict(
            self._read_group(
                domain=[
                    ("id", "not in", self.ids),
                    ("employee_id", "in", self.employee_id.ids),
                    ("state", "not in", ["cancel", "refuse"]),
                    ("leave_type_request_unit", "=", "day"),
                ],
                groupby=["employee_id"],
                aggregates=["id:recordset"],
            )
        )

        resource_calendar = resource_calendar or self.resource_calendar_id

        for leave in self:
            rule = self.env["hr.sandwich.leave.rule"].search(
                [("leave_type_id", "=", leave.holiday_status_id.id)], limit=1
            )

            if rule:
                days, hours = result
                updated_days = leave._apply_sandwich_rule(
                    public_holidays, leaves_by_employee.get(leave.employee_id, []), days
                )
                print("DEBUG: updated_days", updated_days)
                result = (updated_days, hours)
                leave.contains_sandwich_leaves = updated_days != days
            else:
                leave.contains_sandwich_leaves = False
        print("\n\n")
        return result

    def _get_public_holidays(self):
        """Retrieve public holidays based on the company calendar."""
        public_holidays = self.env["resource.calendar.leaves"].search(
            [
                ("resource_id", "=", False),
                ("company_id", "in", self.company_id.ids),
            ]
        )
        return {holiday.date_from.date() for holiday in public_holidays}

    @api.onchange("contains_sandwich_leaves", "request_date_from", "request_date_to", "holiday_status_id", "employee_id")
    def _onchange_contains_sandwich_leaves(self):
        """Show notification if Sandwich Leave is applied."""
        if self.contains_sandwich_leaves:
            return {
                "warning": {
                    "title": _("Warning"),
                    "message": _(
                        "Your leave contains additional sandwich days due to company policy."
                    ),
                    "type": "notification",
                    "sticky": True,  # Ensures the notification remains until dismissed
                }
            }
