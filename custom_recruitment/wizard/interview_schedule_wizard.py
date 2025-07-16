from odoo import models, fields, api, _
from odoo.exceptions import UserError
from pygments.lexer import default


class InterviewScheduleWizard(models.TransientModel):
    _name = 'interview.schedule.wizard'
    _description = 'Schedule Interview Wizard'

    applicant_id = fields.Many2one('hr.applicant', required=True, readonly=True)
    interview_datetime = fields.Datetime("Interview Date & Time", required=True)
    interview_type = fields.Selection([
        ('online', 'Online'),
        ('offline', 'Offline')
    ], string="Interview Type", required=True)
    interview_location = fields.Char("Location", default="Space-O Technology")
    interview_link = fields.Char("Meeting Link")
    interviewer_ids = fields.Many2many('res.users', string="Interviewers", required=True)

    def action_schedule_interview(self):
        print("\nDebug----------------------action_schedule_interview", self.applicant_id)
        for record in self:

            # Send email
            template = self.env.ref('custom_recruitment.interview_invitation_email_template')
            if not template:
                raise UserError("Email template not found.")

            # Add interviewers' emails dynamically
            email_list = [user.email for user in record.interviewer_ids if user.email]
            email_list.append(record.applicant_id.email_from)
            template.email_to = ','.join(email_list)
            template.send_mail(record.applicant_id.id, force_send=True)