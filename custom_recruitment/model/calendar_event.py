from odoo import models, fields, api


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    applicant_id = fields.Many2one('hr.applicant', string="Applicant")

    def write(self, vals):
        res = super().write(vals)
        self._sync_partners_to_applicant(vals)
        return res

    def create(self, vals):
        events = super().create(vals)
        events._sync_partners_to_applicant(vals)
        return events

    def _sync_partners_to_applicant(self, vals):
        if 'partner_ids' not in vals:
            return

        for event in self:
            if not event.applicant_id:
                continue

            applicant = event.applicant_id
            old_user_ids = set(applicant.interviewer_ids.ids)

            new_partner_ids = set(event.partner_ids.ids)
            commands = vals['partner_ids']

            for command in commands:
                if command[0] == 6:  # Replace all
                    new_partner_ids = set(command[2])
                elif command[0] == 4:  # Add one
                    new_partner_ids.add(command[1])
                elif command[0] == 3:  # Remove one
                    new_partner_ids.discard(command[1])
                elif command[0] == 5:  # Remove all
                    new_partner_ids = set()

            # Find corresponding users
            new_users = self.env['res.users'].search([('partner_id', 'in', list(new_partner_ids))])
            new_user_ids = set(new_users.ids)

            # Identify truly new users (not already present)
            users_to_add = new_user_ids - old_user_ids

            # Combine old + new for field update
            final_user_ids = list(old_user_ids.union(new_user_ids))
            applicant.write({
                'interviewer_ids': [(6, 0, list(final_user_ids))]
            })

            # Only send to new users
            if users_to_add:
                applicant.with_context(
                    new_user_ids=list(users_to_add)
                ).action_send_evaluation_portal_link()
