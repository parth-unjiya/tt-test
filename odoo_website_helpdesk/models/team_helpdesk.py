# -*- coding: utf-8 -*-

from odoo import api, fields, models


class TeamHelpDesk(models.Model):
    """Helpdesk team"""
    _name = 'team.helpdesk'
    _description = 'Helpdesk Team'

    name = fields.Char('Name', help='Helpdesk Team Name')
    team_lead_id = fields.Many2one('res.users', string='Team Leader',
                                   help='Team Leader Name',
                                   domain=lambda self: [
                                       ('groups_id', 'in', self.env.ref(
                                           'odoo_website_helpdesk.helpdesk_team_leader').id)])
    member_ids = fields.Many2many('res.users', string='Members',
                                  help='Team Members',
                                  domain=lambda self: [
                                      ('groups_id', 'in', self.env.ref(
                                          'odoo_website_helpdesk.helpdesk_user').id)])
    email = fields.Char('Email', help='Email of the team member.')
    create_task = fields.Boolean(string="Create Task",
                                 help="Task created or not")

    type_ids = fields.Many2many(
        'helpdesk.type',
        relation='ticket_type_team_rel',
        column1='team_id',
        column2='type_id',
        string='Types'
    )

    @api.onchange('team_lead_id')
    def _onchange_team_lead_id(self):
        """Members selection function"""
        fetch_members = self.env['res.users'].search([])
        filtered_members = fetch_members.filtered(
            lambda x: x.id != self.team_lead_id.id)
        return {'domain': {'member_ids':
                               [('id', '=', filtered_members.ids), (
                                   'groups_id', 'in',
                                   self.env.ref('base.group_user').id),
                                ('groups_id', 'not in', self.env.ref(
                                    'odoo_website_helpdesk.helpdesk_team_leader').id)]}}
