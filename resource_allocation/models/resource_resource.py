from odoo import api, fields, models


class ResourceResource(models.Model):
    _inherit = "resource.resource"
    _rec_name = "display_name"

    display_name = fields.Char(compute="_compute_rec_name")

    @api.depends('name', 'employee_id', 'employee_id.department_id')
    def _compute_rec_name(self):
        for resource in self:
            if resource.employee_id:
                resource.display_name = f"{resource.name} - {resource.employee_id.department_id.name}"
            else:
                resource.display_name = resource.name

    avatar_128 = fields.Image(compute="_compute_avatar")
    tt_id = fields.Char(string="TT ID")

    @api.depends('employee_id')
    def _compute_avatar(self):
        for resource in self:
            if resource.employee_id:
                resource.avatar_128 = resource.employee_id and resource.employee_id.avatar_128
            else:
                print("=================>", resource.resource_type)
                resource.avatar_128 = False