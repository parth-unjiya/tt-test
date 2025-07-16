# -*- coding: utf-8 -*-

from odoo import models, fields, api,exceptions


class HrPolicy(models.Model):
    _name = "hr.policy"
    _description = "Policy"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    @api.model
    def default_get(self, fields):
        res = super(HrPolicy, self).default_get(fields)
        print('\n\ndefault get method called')
        if self.env.context.get('default_policy_id'):
            parent_policy = self.env['hr.policy'].sudo().browse(self.env.context['default_policy_id'])
            res.update({
                'name': parent_policy.name,
                'version': str(round(float(parent_policy.version) + 0.1, 1)),
                'effective_date': parent_policy.effective_date,
                'sop_category_id': parent_policy.sop_category_id,
            })

        return res
    name = fields.Char(
        required=True,
    )
    
    effective_date = fields.Date(string="Effective Date",default=fields.Date.context_today)
    description = fields.Html("Description")
    is_visible = fields.Boolean(default=True,string='Is Visible')

    state = fields.Selection(
        [("draft", "Draft"), ("approved", "Approved"), ("obsolete", "Obsolete")],
        string="Status",
        default="draft",
    )

    policy_id = fields.Many2one("hr.policy", string="Parent Policy", help="Select Parent id.")
    sop_category_id = fields.Many2one("sop.category", string="Sop Category")
    is_published = fields.Boolean(string="Published", default=False)
    website_url = fields.Char('Website URL', compute='_compute_website_url')
    version = fields.Char(string="Version", required=True, default="1.0")

    child_policy_count = fields.Integer(
        string='Child Policies',
        compute='_compute_child_policy_count'
    )
    child_policy_ids = fields.One2many(
        'hr.policy', 
        'policy_id', 
        string='Child Policies'
    )

    def _compute_website_url(self):
        for policy in self:
            policy.website_url = f"/hr_policy"

    def action_publish(self):
        for record in self:
            record.is_published = True

    def action_unpublish(self):
        for record in self:
            record.is_published = False
    
    def open_website_url(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': self.website_url,
            'target': 'new',
        }


    def action_approve(self):
        for record in self:
            parent_records = self.env['hr.policy'].search([('id', '=', record.policy_id.id)])
            # print('\n\n child_records:', (parent_records.name + "(" + parent_records.version + ")"))
            
            # Gather names of non-obsolete parent records
            non_obsolete_records = parent_records.filtered(lambda p: p.state != 'obsolete')
            
            if non_obsolete_records:
                # Join the names into a single string for the error message
                parent_names = (parent_records.name + "(" + parent_records.version + ")")
                raise exceptions.ValidationError(
                    'Cannot mark this record as "Approve" because the following parent records are not obsolete: %s. Please obsolete them first.' % parent_names)
        
        # Set the state to "approved" if all parent records are obsolete
        self.state = "approved"

    def action_obsolete(self):
       
        self.state = 'obsolete'
        self.is_published = False

    def open_child_form(self):
        self.is_visible = True
        return {
            'type': 'ir.actions.act_window',
            'name': 'HR Policy',
            'res_model': 'hr.policy',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_policy_id': self.id, 
                'default_is_visible': self.is_visible,
            },
        }
    
    @api.model_create_multi
    def create(self, vals):
        context = dict(self.env.context)
        print('\n\n --------context',context)
        context['default_is_visible'] = True
        print('\n\n*******self visible*******',context['default_is_visible']) 
        return super(HrPolicy, self).create(vals)

    def _compute_child_policy_count(self):
        for record in self:
            record.child_policy_count = len(record.child_policy_ids)

    def action_view_child_policies(self):
        self.ensure_one()
        return {
            'name': 'Child Policies',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.policy',
            'view_mode': 'tree,form',
            'domain': [('policy_id', '=', self.id)],
            'context': {'default_policy_id': self.id},
            'target': 'current',
        }