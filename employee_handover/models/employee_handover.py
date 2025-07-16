from odoo import fields, models, api, tools, _


class EmployeeHandover(models.Model):
    _name = 'employee.handover'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Employee Handover'
    _rec_name = 'employee_id'

    def _get_data_hr(self):
        return [('project_id', '=', self.env.ref('employee_handover.hr_project').id)]

    def _get_data_admin(self):
        return [('project_id', '=', self.env.ref('employee_handover.admin_project').id)]

    def _get_data_project(self):
        return [('project_id.is_handover', '=', False)]

    employee_id = fields.Many2one('hr.employee', 'Employee')
    handover_employee_id = fields.Many2one('hr.employee', 'To Employee')
    employee_department_id = fields.Many2one('hr.department', 'Department', related='employee_id.department_id')
    releaving_date = fields.Date('Releaving Date')

    manager_id = fields.Many2one('res.users', 'Manager')
    approver_id = fields.Many2one('hr.employee', 'Approver', related='employee_department_id.manager_id')

    description = fields.Html('Remarks')
    status = fields.Selection(
        [('pending', 'Pending'), ('initiated', 'Initiated'), ('backout', 'Back Out'), ('cancelled', 'Cancelled'),
         ('completed', 'Completed'), ('rollback', 'Rollback')], 'Status', default='pending')

    hr_task_ids = fields.One2many('project.task', 'employee_handover_id', string='HR Tasks', domain=_get_data_hr)
    admin_task_ids = fields.One2many('project.task', 'employee_handover_id', string='Admin Tasks', domain=_get_data_admin)
    project_task_ids = fields.One2many('project.task', 'employee_handover_id', string='Project Tasks', domain=_get_data_project)
    task_count = fields.Integer(compute='_compute_task_count', string='Tasks')
    tt_id = fields.Char('TT ID')

    def _compute_task_count(self):
        for handover in self:
            tasks = self.env['project.task'].search([('employee_handover_id', '=', handover.id)])
            if handover.env.user.has_group('employee_handover.group_technique_admin') and handover.env.user.has_group('employee_handover.group_technique_hr'):
                tasks = self.env['project.task'].search([('employee_handover_id', '=', handover.id)])
            elif self.env.user.has_group('employee_handover.group_technique_admin'):
                tasks = self.env['project.task'].search([('employee_handover_id', '=', handover.id), ('project_id', '=', self.env.ref('employee_handover.admin_project').id)])
            elif self.env.user.has_group('employee_handover.group_technique_hr'):
                tasks = self.env['project.task'].search([('employee_handover_id', '=', handover.id), ('project_id', '=', self.env.ref('employee_handover.hr_project').id)])
            elif not self.env.user.has_group('employee_handover.group_technique_admin') and not self.env.user.has_group(
                    'employee_handover.group_technique_hr'):
                tasks = self.env['project.task'].search([('employee_handover_id', '=', handover.id), ('project_id.is_handover', '=', False)])
            print("Debug===========================================tasks", tasks)
            handover.task_count = len(tasks)

    def action_view_tasks(self):
        domain = [('employee_handover_id', '=', self.id)]
        if self.env.user.has_group('employee_handover.group_technique_admin') and self.env.user.has_group('employee_handover.group_technique_hr'):
            domain = [('employee_handover_id', '=', self.id)]

        elif self.env.user.has_group('employee_handover.group_technique_admin'):
            domain = [('employee_handover_id', '=', self.id), ('project_id', '=', self.env.ref('employee_handover.admin_project').id)]

        elif self.env.user.has_group('employee_handover.group_technique_hr'):
            domain = [('employee_handover_id', '=', self.id), ('project_id', '=', self.env.ref('employee_handover.hr_project').id)]

        elif not self.env.user.has_group('employee_handover.group_technique_admin') and not self.env.user.has_group('employee_handover.group_technique_hr'):
            domain = [('employee_handover_id', '=', self.id), ('project_id.is_handover', '=', False)]
        print("Debug===========================================domain", domain)
        return {
            'name': _('Tasks'),
            'view_mode': 'tree,form',
            'res_model': 'project.task',
            'type': 'ir.actions.act_window',
            'domain': domain,
        }

    def action_default_handover(self):
        print("-----------------vals------------------", self.id)
        hr_project = self.env.ref('employee_handover.hr_project')
        admin_project = self.env.ref('employee_handover.admin_project')
        for task in hr_project.task_ids + admin_project.task_ids:
            if not task.parent_id:
                print("-----------------task------------------", task)
                task_vals = {
                    'name': task.name + "Handover of " + self.employee_id.name,
                    'parent_id': task.id,
                    'project_id': task.project_id.id,
                    # 'user_ids': task.user_ids[0].id,
                    'employee_handover_id': self.id,
                    # 'status': 'pending'
                }
                print("-----------------task_vals------------------", task_vals)
                task.child_ids.create(task_vals)


class ProjectProject(models.Model):
    _inherit = 'project.project'

    tt_id = fields.Char('TT ID')
    is_handover = fields.Boolean(string='Is Handover', default=False)


class ProjectTask(models.Model):
    _inherit = 'project.task'

    tt_id = fields.Char('TT ID')
    employee_handover_id = fields.Many2one('employee.handover', 'Employee Handover')
    employee_id = fields.Many2one('hr.employee', 'From Employee', related='employee_handover_id.employee_id')
