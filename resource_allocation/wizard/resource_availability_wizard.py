from datetime import datetime, date, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError

DEFAULT_DAILY_CAPACITY = 8.5


class ResourceAvailabilityWizard(models.TransientModel):
    _name = "resource.availability.wizard"
    _description = "Check Resource Availability"

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)

        if (
            defaults.get("resource_id")
            and defaults.get("date_from")
            and defaults.get("date_to")
        ):
            wizard = self.new(defaults)
            wizard.action_check_availability()
            # refresh fields after compute
            for field in self._fields:
                if field not in defaults and field in wizard:
                    defaults[field] = wizard[field]

        return defaults

    resource_id = fields.Many2one("resource.resource", required=True, readonly=True)
    date_from = fields.Date(required=True, readonly=True)
    date_to = fields.Date(required=True, readonly=True)
    availability_line_ids = fields.One2many(
        "resource.availability.line", "wizard_id", string="Availability", readonly=True
    )
    daily_capacity = fields.Float(
        string="Daily Capacity (Hours)",
        default=DEFAULT_DAILY_CAPACITY,
        required=True,
        help="Assumed daily working capacity for the resource in hours."
    )

    def action_check_availability(self):
        """
        Computes and displays the resource availability based on the wizard's criteria.
        This method is intended to be called by a button on the wizard.
        """
        self.ensure_one()
        self.compute_availability_lines()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Resource Availability'),
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
        
    def compute_availability_lines(self):
        """
        Core logic to compute availability lines.
        Populates self.availability_line_ids.
        """
        self.ensure_one()
        Allocation = self.env['resource.allocation']
        line_vals_list = []

        # Validate date range to prevent excessive computation if necessary
        if (self.date_to - self.date_from).days > 365: # Example limit: 1 year
            raise UserError(_("The date range is too large. Please select a smaller period (e.g., up to 1 year)."))

        # Fetch all relevant allocations for the resource within the broad date range once
        # Assumes 'start_date' and 'end_date' on resource.allocation are Datetime fields
        all_allocations_in_range = Allocation.search([
            ('resource_id', '=', self.resource_id.id),
            ('start_date', '<=', fields.Datetime.to_string(datetime.combine(self.date_to, datetime.max.time()))),
            ('end_date', '>=', fields.Datetime.to_string(datetime.combine(self.date_from, datetime.min.time())))
        ])

        current_date_iter = self.date_from
        while current_date_iter <= self.date_to:
            day_start_dt = datetime.combine(current_date_iter, datetime.min.time())
            day_end_dt = datetime.combine(current_date_iter, datetime.max.time())

            # Filter allocations for the current day from the pre-fetched list
            day_allocations = [
                alloc for alloc in all_allocations_in_range
                if alloc.start_date <= day_end_dt and alloc.end_date >= day_start_dt
            ]
            
            daily_total_allocated_hours = 0.0
            # Store data as {project_record: hours}
            projects_on_day_data = {} 

            if day_allocations:
                for alloc in day_allocations:
                    # Assumes 'project_id' (Many2one) and 'hours_per_day' (Float) exist on 'resource.allocation'
                    project_on_allocation = getattr(alloc, 'project_id', self.env['project.project'])
                    hours_for_this_alloc_on_this_day = float(getattr(alloc, 'hours_per_day', 0.0) or 0.0)

                    current_project_hours = projects_on_day_data.get(project_on_allocation, 0.0)
                    projects_on_day_data[project_on_allocation] = current_project_hours + hours_for_this_alloc_on_this_day
                    daily_total_allocated_hours += hours_for_this_alloc_on_this_day
            
            daily_remaining_hours = self.daily_capacity - daily_total_allocated_hours

            if projects_on_day_data:
                for project, project_hours in projects_on_day_data.items():
                    line_vals_list.append((0, 0, {
                        'date': current_date_iter,
                        'project_id': project.id if project and project.exists() else False,
                        'allocated_hours': project_hours,
                        'remaining_hours': daily_remaining_hours,
                    }))
            else:
                # No allocations for this resource on this day, show full availability
                line_vals_list.append((0, 0, {
                    'date': current_date_iter,
                    'project_id': False,
                    'allocated_hours': 0.0,
                    'remaining_hours': self.daily_capacity,
                }))
            
            current_date_iter += timedelta(days=1)

        self.availability_line_ids.unlink()
        self.availability_line_ids = line_vals_list


class ResourceAvailabilityLine(models.TransientModel):
    _name = "resource.availability.line"
    _description = "Resource Daily Availability"
    _order = "date, project_id"

    wizard_id = fields.Many2one("resource.availability.wizard")
    date = fields.Date(string="Date", readonly=True)
    project_id = fields.Many2one("project.project", string="Project", readonly=True)
    allocated_hours = fields.Float(
        string="Project Allocated Hours",
        readonly=True,
        help="Hours allocated to this specific project on this date.",
    )
    remaining_hours = fields.Float(
        string="Daily Remaining Hours",
        readonly=True,
        help="Total remaining work capacity for the resource on this date, across all projects.",
    )
