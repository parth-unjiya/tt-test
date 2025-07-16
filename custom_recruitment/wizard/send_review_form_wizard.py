import uuid

from odoo import models, fields, api, _
from datetime import datetime, timedelta


class SendReviewFormWizard(models.TransientModel):
    _name = "send.review.form.wizard"
    _description = "Send Review Form Wizard"

    def default_get(self, fields_list):
        res = super(SendReviewFormWizard, self).default_get(fields_list)
        if "applicant_id" in res:
            applicant = self.env["hr.applicant"].browse(res["applicant_id"])
            res["interviewer_ids"] = (
                [(6, 0, applicant.interviewer_ids.ids)]
                if applicant.interviewer_ids
                else []
            )
        return res

    interviewer_ids = fields.Many2many(
        "res.users", string="Interviewers", required=True
    )
    applicant_id = fields.Many2one("hr.applicant", required=True, readonly=True)

    def action_send_portal_link(self):
        for rec in self:
            base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
            template = self.env.ref(
                "custom_recruitment.email_template_candidate_evaluation"
            )

            for interviewer in rec.interviewer_ids:
                # Generate unique token for each interviewer
                token = str(uuid.uuid4())
                expiry = fields.Datetime.now() + timedelta(days=2)

                # Create evaluation record if not exists
                eval_record = self.env["candidate.evaluation"].search(
                    [
                        ("applicant_id", "=", rec.applicant_id.id),
                        ("interviewer_id", "=", interviewer.id),
                    ],
                    limit=1,
                )

                if not eval_record:
                    self.env["candidate.evaluation"].create(
                        {
                            "applicant_id": rec.applicant_id.id,
                            "interviewer_id": interviewer.id,
                            "token": token,
                            "token_expiry": expiry,
                        }
                    )
                else:
                    eval_record.write(
                        {
                            "token": token,
                            "token_expiry": expiry,
                        }
                    )

                portal_url = f"{base_url}/candidate/evaluation/form/{token}"

                # Send email to interviewer
                template.with_context(
                    portal_url=portal_url,
                    interviewer_name=interviewer.name,
                    employee_name=rec.applicant_id.name,
                    expiry_date=expiry,
                    user_email=self.env.user.email,
                    user_name=self.env.user.name,
                ).send_mail(
                    rec.applicant_id.id,
                    email_values={"email_to": interviewer.email},
                    force_send=True,
                )
