from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta, datetime
from random import randint
import math


class ResourceAllocation(models.Model):
    _name = "resource.allocation"
    _description = "Resource Allocation"
    _inherit = "mail.thread"

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char(
        string="Name", compute="_compute_name",
    )

    tt_id = fields.Char(string="TT ID")
    avatar_128 = fields.Image(compute='_compute_avatar')
    color = fields.Integer('Color Index', default=_get_default_color)

    project_id = fields.Many2one(
        "project.project",
        string="Project",
        required=True,
        help="Select the project to which the resource is allocated.",
    )
    task_id = fields.Many2one(
        "project.task",
        string="Task",
        domain="[('project_id', '=', project_id), ('parent_id', '=', False)]",
        help="Select the task within the chosen project.",
    )
    resource_type = fields.Selection(
        [
            ("user", "Human"),
            ("material", "Material"),
        ],
        string="Resource Type", default="user",
        required=True,
        help="Specify whether the resource is a human or material.",
    )
    resource_id = fields.Many2one(
        "resource.resource",
        string="Resource",
        required=True,
        domain="[('resource_type', '=', resource_type)]",
        help="Select the specific resource based on the type.",
    )
    user_id = fields.Many2one(
        "res.users", related="resource_id.user_id", string="User", store=True
    )
    allocation_hours = fields.Float(
        string="Allocation (Hours)",
        required=True,
        compute="_compute_allocation_hours",
        inverse="_inverse_sync_DATES_HOURS",
        store=True,
        help="Specify the number of hours allocated for this resource.",
    )
    start_date = fields.Datetime(
        string="Start Date", help="Specify when the allocation starts."
    )
    end_date = fields.Datetime(
        string="End Date", 
        help="Specify when the allocation ends.", 
        compute="_compute_end_date",
        inverse="_inverse_sync_DATES_HOURS",
        store=True,
    )
    notes = fields.Html(string="Notes")
    state = fields.Selection([
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('approve', 'Approved'),
            ('reject', 'Reject'),
        ], string="Status", default='draft', tracking=True)


    def _get_hour_slots(self):
        return [(str(i / 2), f"{i / 2:.1f} Hours") for i in range(1, 25)]  # 0.5 to 12.0 hours

    hours_per_day = fields.Selection(
        selection=lambda self: self._get_hour_slots(),
        string="Hours Per Day",
    )

    @api.depends('start_date', 'end_date', 'hours_per_day')
    def _compute_allocation_hours(self):
        """Calculate allocation_hours from start_date, end_date, and hours_per_day."""
        mandatoryDay = self.env['hr.leave.mandatory.day']
        for rec in self:
            if rec.start_date and rec.end_date and rec.hours_per_day:
                if rec.end_date < rec.start_date:
                    rec.allocation_hours = 0
                    continue
                try:
                    hpd = float(rec.hours_per_day)
                    if hpd <= 0:
                        rec.allocation_hours = 0
                        continue
                except (ValueError, TypeError):
                    rec.allocation_hours = 0
                    continue

                total_allocated_hours = 0.0
                current_day = rec.start_date.date()
                while current_day <= rec.end_date.date():
                    is_weekday = current_day.weekday() < 5  # Monday (0) to Friday (4)

                    # Check if the current day is a mandatory day
                    mandatory_day = mandatoryDay.search([
                        ('start_date', '=', current_day),
                        '|',
                        ('company_id', '=', False),
                        ('company_id', '=', self.env.company.id),
                    ])

                    if is_weekday or mandatory_day:
                        hours_on_this_day = hpd
                        if current_day == rec.start_date.date() and current_day == rec.end_date.date():
                            duration_seconds = (rec.end_date - rec.start_date).total_seconds()
                            hours_on_this_day = min(max(0, duration_seconds / 3600), hpd)
                        # Simplified: assumes full HPD for start/end days if part of a multi-day range.
                        # For more precision on partial first/last days in a multi-day range, refine here.
                        total_allocated_hours += hours_on_this_day
                    current_day += timedelta(days=1)
                rec.allocation_hours = total_allocated_hours
            else:
                if not rec.allocation_hours:
                    rec.allocation_hours = 0.0

    @api.depends('start_date', 'allocation_hours', 'hours_per_day')
    def _compute_end_date(self):
        """Calculate end_date from start_date, allocation_hours, and hours_per_day."""
        MandatoryDay = self.env['hr.leave.mandatory.day']
        for rec in self:
            if rec.start_date and rec.allocation_hours > 0 and rec.hours_per_day:
                try:
                    hpd = float(rec.hours_per_day)
                    if hpd <= 0:
                        rec.end_date = False
                        continue
                except (ValueError, TypeError):
                    rec.end_date = False
                    continue

                hours_remaining = rec.allocation_hours
                current_datetime = rec.start_date
                calculated_end_datetime = rec.start_date
                # Safety break for loop iterations
                max_iterations = (rec.allocation_hours / (hpd if hpd > 0 else 1)) + 30 
                # Increased safety margin for very small hpd or large allocation_hours
                max_iterations = math.ceil(max_iterations) if max_iterations > 0 else 365 * 2 # Minimum safety net
                
                day_iteration_count = 0

                while hours_remaining > 0 and day_iteration_count < max_iterations:
                    day_iteration_count += 1
                    
                    is_working_day = False

                    if current_datetime.weekday() < 5:
                        is_working_day = True
                    else:
                        mandatory_day = MandatoryDay.search([
                            ('start_date', '=', current_datetime.date()),
                            '|',
                            ('company_id', '=', False),
                            ('company_id', '=', self.env.company.id),
                        ])
                        if mandatory_day:
                            is_working_day = True

                    if is_working_day:
                        hours_to_work_this_day = min(hours_remaining, hpd)
                        day_start_time_obj = rec.start_date.time()
                        if current_datetime.date() > rec.start_date.date():
                            calculated_end_datetime = datetime.combine(current_datetime.date(), day_start_time_obj) + timedelta(hours=hours_to_work_this_day)
                        else:
                            calculated_end_datetime = current_datetime + timedelta(hours=hours_to_work_this_day)
                        hours_remaining -= hours_to_work_this_day
                    
                    if hours_remaining > 0:
                        current_datetime = (current_datetime + timedelta(days=1)).replace(
                            hour=rec.start_date.hour, minute=rec.start_date.minute,
                            second=rec.start_date.second, microsecond=rec.start_date.microsecond
                        )
                
                if hours_remaining <= 0:
                    rec.end_date = calculated_end_datetime
                else: 
                    rec.end_date = False # Could indicate an issue like loop termination by safety break
            elif rec.allocation_hours <= 0:
                rec.end_date = rec.start_date
            else:
                if not rec.end_date:
                     rec.end_date = False

    def _inverse_sync_DATES_HOURS(self):
        """Allows manual setting of allocation_hours or end_date, triggering recomputation of the other."""
        pass

    def action_confirm(self):
        self.trigger_notification()
        self.write({'state': 'confirmed'})

    def action_approve(self):
        self.write({'state': 'approve'})

    def action_reject(self):
        self.write({'state': 'reject'})

    def action_draft(self):
        self.write({'state': 'draft'})

    @api.model
    def trigger_notification(self):
        # Fetch the OdooBot partner
        odoobot_partner = self.env['res.partner'].search([('name', '=', 'OdooBot'), ('active', '=', False)], limit=1)
        print("Debug------------------------ odoobot_partner ----------------------->", odoobot_partner)
        if not odoobot_partner:
            print("OdooBot partner not found!")
            return False
        # Get the group
        group = self.env.ref('custom_dashboard.group_dashboard_resource_manager')
        print("Debug------------------------ group ----------------------->", group)

        # Fetch users belonging to the specified group
        user_ids = self.env['res.users'].search([('groups_id', 'in', [group.id])])
        print("Debug------------------------ user_ids ----------------------->", user_ids)

        for user in user_ids:
            # Create the notification
            user_partner = user.partner_id

            # Search for the channel between OdooBot and the user
            channel = self.env['discuss.channel'].search([
                ('channel_partner_ids', 'in', [odoobot_partner.id]),
                ('channel_partner_ids', 'in', [user_partner.id]),
            ], limit=1)

            print("Debug------------------------ channel ----------------------->", channel)

            # channel_msg = channel.sudo().message_post(
            #     message_type='comment',
            #     subtype_xmlid='mail.mt_note',
            #     subject='New Resource Allocation has been requested',
            #     body=f'New resource allocation for {self.resource_id.name} has been requested for {self.allocation_hours} hours in {self.project_id.name}.',
            #     author_id=odoobot_partner.id,
            # )
            # print("Debug------------------------ channel_msg ----------------------->", channel_msg)

            self.message_notify(
                partner_ids=[user_partner.id],
                subject='New Resource Allocation has been requested',
                body=f'New resource allocation for {self.resource_id.name} has been requested for {self.allocation_hours} hours in {self.project_id.name}.',
                res_id=self.id,
                model='resource.allocation',
                author_id=odoobot_partner.id,
                record_name=self.project_id.name,
            )


            # Send the notification to the user
            # bus_id = self.env['bus.bus']._sendone(
            #     (self._cr.dbname, channel.id),
            #     'sample_notification',
            #     message='New Resource Allocation has been requested'
            # )
            # print("Debug------------------------ bus_id ----------------------->", bus_id)

    # IN Below Methods Add Project id if not exists from task
    # In That add user_id if not exists in project.task
    # @api.model_create_multi
    # def create(self, vals_list):
    #     for vals in vals_list:
    #         if "task_id" in vals and not vals.get("project_id"):
    #             task = self.env["project.task"].browse(vals["task_id"])
    #             if task.exists():
    #                 vals["project_id"] = task.project_id.id

    #     records = super().create(vals_list)

    #     for record in records:
    #         if record.task_id and record.user_id and record.user_id not in record.task_id.user_ids:
    #             record.task_id.user_ids = [(4, record.user_id.id)]
    #     return records

    # def write(self, vals):
    #     if "task_id" in vals:
    #         for record in self:
    #             if record.task_id.id != vals["task_id"]:
    #                 task = self.env["project.task"].browse(vals["task_id"])
    #                 if task.exists():
    #                     vals["project_id"] = task.project_id.id
    #                 break

    #     res = super().write(vals)

    #     for record in self:
    #         if record.task_id and record.user_id and record.user_id not in record.task_id.user_ids:
    #             record.task_id.user_ids = [(4, record.user_id.id)]
    #     return res
    
    @api.depends('project_id', 'resource_id')
    def _compute_name(self):
        """Compute the name of the allocation as 'Project Name [Resource Name]'"""
        for allocation in self:
            if allocation.project_id and allocation.resource_id:
                allocation.name = f"{allocation.project_id.name} [{allocation.resource_id.name}]"
            else:
                allocation.name = "Unnamed Allocation"

    # --- VALIDATION ---
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.end_date < rec.start_date:
                raise ValidationError(_("End Date cannot be before Start Date."))

    @api.constrains('allocation_hours')
    def _check_allocation_hours(self):
        for rec in self:
            if rec.allocation_hours < 0:
                raise ValidationError(_("Allocation (Hours) cannot be negative."))