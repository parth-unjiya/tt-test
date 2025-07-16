from odoo import models, fields, api


class ProjectModule(models.Model):
    _name = 'project.module'
    _description = 'Project Module'

    name = fields.Char(string='Module Name', required=True)