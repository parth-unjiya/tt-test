# -*- coding: utf-8 -*-

from datetime import date 
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Project(models.Model):
    _inherit = "project.project"

    resource_allocation_ids = fields.One2many(
        "resource.allocation", "project_id", string="Resource Allocations"
    )


class ProjectTask(models.Model):
    _inherit = "project.task"

    resource_allocation_ids = fields.One2many(
        "resource.allocation", "task_id", string="Resource Allocations"
    )

    start_date = fields.Datetime(
        string="Start Date",
    )
    
    # @api.model_create_multi
    # def create(self, vals_list):
    #     """Automatically create resource allocations based on user_ids."""
    #     tasks = super(ProjectTask, self).create(vals_list)

    #     for task in tasks:
    #         # Create resource allocations for each user in user_ids
    #         if task.user_ids and task.project_id:
    #             allocations = []
    #             for user in task.user_ids:
    #                 if user.employee_id and user.employee_id.resource_id:
    #                     allocations.append({
    #                         "task_id": task.id,
    #                         "project_id": task.project_id.id,
    #                         "resource_type": "user",
    #                         "resource_id": user.employee_id.resource_id.id,
    #                         "allocation_hours": task.allocated_hours,
    #                         "start_date": task.start_date,
    #                         "end_date": task.date_deadline,
    #                     })
    #                 else:
    #                     # Log a warning or raise an error if necessary
    #                     _logger.warning(
    #                         f"Skipping allocation for user {user.name} as resource_id is missing."
    #                     )
    #             # Bulk create resource allocations to optimize performance
    #             if allocations:
    #                 self.env["resource.allocation"].create(allocations)

    #     return tasks

    # def write(self, vals):
    #     """Automatically update resource allocations based on user_ids, allocated_hours, and date_deadline."""
    #     res = super(ProjectTask, self).write(vals)

    #     for task in self:
    #         new_user_ids = set()
    #         remove_user_ids = set()

    #         if "user_ids" in vals:
    #             user_ids_commands = vals["user_ids"]
    #             for command in user_ids_commands:
    #                 if command[0] == 6:
    #                     new_user_ids = set(command[2])
    #                 elif command[0] == 4:
    #                     new_user_ids.add(command[1])
    #                 elif command[0] == 3:
    #                     remove_user_ids.add(command[1])

    #         # Existing user IDs in current allocations
    #         existing_user_ids = set(
    #             task.resource_allocation_ids.mapped("resource_id.user_id.id")
    #         )

    #         # Determine users to add or remove
    #         users_to_add = new_user_ids
    #         users_to_remove = remove_user_ids

    #         # Remove resource allocations for users no longer in user_ids
    #         if users_to_remove and "personal_stage_id" not in vals:
    #             data = task.resource_allocation_ids.filtered(
    #                 lambda ra: ra.resource_id.user_id.id in users_to_remove
    #             )
    #             data.unlink()

    #         # Add new resource allocations for added users
    #         new_allocation_hours = vals.get("allocated_hours", None)
    #         # Optional hours update
    #         new_deadline = vals.get("date_deadline", task.date_deadline)
    #         # Updated deadline
    #         new_start_date = task.start_date

    #         for user_id in users_to_add:
    #             # Search for the resource associated with the user_id
    #             resource = self.env["resource.resource"].search([("user_id", "=", user_id)], limit=1)
                
    #             if resource:
    #                 # Create resource allocation only if a valid resource is found
    #                 self.env["resource.allocation"].create(
    #                     {
    #                         "task_id": task.id,
    #                         "project_id": task.project_id.id,
    #                         "resource_id": resource.id,
    #                         "resource_type": "user",
    #                         "allocation_hours": new_allocation_hours,
    #                         "start_date": new_start_date,
    #                         "end_date": new_deadline,
    #                     }
    #                 )
    #             else:
    #                 # Log a warning if no resource is found for the user_id
    #                 _logger.warning(f"No resource found for user_id {user_id}. Allocation skipped.")
                

    #         # Handle allocated hours changes
    #         if "allocated_hours" in vals:
    #             for allocation in task.resource_allocation_ids:
    #                 allocation.allocation_hours = new_allocation_hours

    #         # Handle deadline changes
    #         if "date_deadline" in vals:
    #             for allocation in task.resource_allocation_ids:
    #                 allocation.end_date = new_deadline

    #     return res
