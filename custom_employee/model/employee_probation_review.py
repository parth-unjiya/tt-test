from odoo import fields, models, api, tools, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

import uuid

class EmployeeProbationReview(models.Model):
    _name = "hr.employee.probation.review"
    _description = "Probation employee review data"

    tt_id = fields.Char(string="TT ID")
    employee_id = fields.Many2one(
        "hr.employee", string="Employee", default=lambda self: self.employee_id
    )
    reviewer_id = fields.Many2one("res.users", string="Reviewer")
    reviewer_ids = fields.Many2many("res.users", string="Reviewers")
    start_date = fields.Datetime(string="Start Date")
    end_date = fields.Datetime(string="End Date")
    review_type = fields.Selection(
        [
            ('1', '1st Month'),
            ('2', '2nd Month'),
            ('3', '3rd Month'),
            ('4', '4th Month'),
            ('5', '5th Month'),
            ('6', '6th Month'),
            ('7', '7th Month'),
            ('8', '8th Month'),
            ('9', '9th Month'),
            ('10', '10th Month'),
            ('11', '11th Month'),
            ('12', '12th Month'),
        ],
        string="Review Type",
    )
    survey_id = fields.Many2one(
        "survey.survey",
        string="Select Opinion Form",
        domain=[("is_review_form", "=", True)],
        help="Survey to send to the Reviewer",
    )
    is_done = fields.Boolean(string="Is done")
    review_status = fields.Selection(
        [("sent", "Sent"), ("done", "Done")], 
        string="Review Status", 
        readonly=False, 
        default="sent"
    )

    review_line_ids = fields.One2many(
        "employee.probation.review.line", 
        "review_id", 
        string="Reviewers Lines"
    )

    def action_send_portal_link(self):
        for rec in self:
            if not rec.reviewer_ids:
                raise UserError("Reviewers are required.")

            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            template = self.env.ref("custom_employee.employee_probation_review_email_template")

            for reviewer in rec.reviewer_ids:
                token = str(uuid.uuid4())
                expiry = fields.Datetime.now() + timedelta(days=2)

                # Create line entry
                line = self.env['employee.probation.review.line'].create({
                    'review_id': rec.id,
                    'reviewer_id': reviewer.id,
                    'token': token,
                    'token_expiry': expiry,
                    'review_status': 'sent'
                })

                portal_url = f"{base_url}/review/form/{token}"

                template.with_context(
                    portal_url=portal_url,
                    reviewer_name=reviewer.name,
                    employee_name=rec.employee_id.name,
                    review_type=rec.review_type,
                    token_expiry=expiry,
                    user_email = self.env.user.email, 
                    user_name = self.env.user.name
                ).send_mail(rec.id, email_values={
                    'email_to': reviewer.email
                }, force_send=True)

            rec.review_status = 'sent'


    # tot_comp_survey = fields.Integer(
    #     string="Count Answers",
    #     compute="_compute_completed_survey",
    #     help="Number of Answers",
    # )

    # def action_send(self):
    #     """This function will start the review by sending emails to the
    #     corresponding employees specified in the probation"""
    #     send_count = 0
    #     baseurl = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
    #     deadline = self.end_date + timedelta(days=5)
    #     print(baseurl, self.reviewer_id.partner_id.email)
    #     print("------------", self.reviewer_id.partner_id.id)
    #     for reviewer in self.reviewer_ids:
    #         response = self.survey_id._create_answer(
    #             survey_id=self.survey_id.id,
    #             deadline=deadline,
    #             partner=reviewer,
    #             email=reviewer.email,
    #             review_id=self.ids[0],
    #         )
    #         url = response.get_start_url()
    #         mail_content = f"""
    #         Dear {reviewer.name},
    #         <br><br>
    #         Please fill out the following review form related to {self.employee_id.name}'s 
    #         probation review for the {self._compute_string()}.
    #         <br><br>
    #         <a href="{baseurl}{url}">Click here to access the review form</a>
    #         <br><br>
    #         Please submit your response by: {deadline}
    #         """
    #         values = {
    #             "model": "hr.employee.probation.review",
    #             "res_id": self.ids[0],
    #             "subject": f"Probation Review for {self.employee_id.name}",
    #             "recipient_ids": reviewer.partner_id,
    #             "body_html": mail_content,
    #             "parent_id": None,
    #             "email_from": self.env.user.email or None,
    #             "auto_delete": False,
    #             "email_to": reviewer.partner_id.email,
    #         }
    #         result = self.env["mail.mail"].sudo().create(values)._send()

    #         if result is True:
    #             send_count += 1
    #             self.review_status = "sent"

    # def action_get_answers(self):
    #     """This function will return all the answers posted related to
    #     this review."""
    #     tree_id = (
    #         self.env["ir.model.data"]._xmlid_to_res_id(
    #             "survey.survey_user_input_view_tree"
    #         )
    #         or False
    #     )
    #     form_id = (
    #         self.env["ir.model.data"]._xmlid_to_res_id(
    #             "survey.survey_user_input_view_form"
    #         )
    #         or False
    #     )
    #     print(">>>>>--------tree", tree_id, form_id)
    #     return {
    #         "model": "ir.actions.act_window",
    #         "name": "Answers",
    #         "type": "ir.actions.act_window",
    #         "view_mode": "form,tree",
    #         "res_model": "survey.user_input",
    #         "views": [(tree_id, "tree"), (form_id, "form")],
    #         "domain": [("state", "=", "done"), ("review_id", "=", self.ids[0])],
    #     }

    # def _compute_completed_survey(self):
    #     """Method _compute_completed_survey will compute the completed survey"""
    #     for rec in self:
    #         answers = self.env["survey.user_input"].search(
    #             [("state", "=", "done"), ("review_id", "=", rec.id)]
    #         )
    #         rec.tot_comp_survey = len(answers)
    #         if len(answers) != 0:
    #             rec.review_status = "done"
    #             if rec.employee_id.department_id.name == "Manager":
    #                 if rec.review_type == "sixth":
    #                     rec.is_done = True
    #                     rec.employee_id.is_done = True
    #             else:
    #                 if rec.review_type == "fourth":
    #                     rec.is_done = True
    #                     rec.employee_id.is_done = True

    # def _compute_string(self):
    #     selected_string = dict(self._fields.get("review_type").selection).get(
    #         self.review_type
    #     )
    #     return selected_string


class EmployeeProbationReviewLine(models.Model):
    _name = "employee.probation.review.line"
    _description = "Review Line per Reviewer"

    reviewer_id = fields.Many2one("res.users", string="Reviewer", required=True)
    review_id = fields.Many2one("hr.employee.probation.review", string="Probation Review", ondelete="cascade")
    name = fields.Char(string="Reviewer Name", related="review_id.employee_id.name")
    review_type = fields.Selection(related="review_id.review_type", store=True, readonly=True)

    review_status = fields.Selection([("sent", "Sent"), ("done", "Done")], string="Status", default="sent")

    # Portal
    token = fields.Char("Portal Token")
    token_expiry = fields.Datetime("Token Expiry Time")
    portal_filled = fields.Boolean("Portal Form Submitted", default=False)

    task_ids = fields.One2many('probation.review.task', 'review_line_id', string="Review Tasks")
    improve_ids = fields.One2many('probation.review.improve', 'review_line_id', string="Improvement Areas")
    summary = fields.Text(string="Overall Performance Summary")

    # Ratings (SECTION 1(A))
    quality_accuracy = fields.Selection([
        ('1', 'Improvement Required'), ('2', 'Average'),
        ('3', 'Good'), ('4', 'Excellent')],
        string="Quality and Accuracy")
    efficiency = fields.Selection([
        ('1', 'Improvement Required'), ('2', 'Average'),
        ('3', 'Good'), ('4', 'Excellent')],
        string="Efficiency")
    attendance = fields.Selection([
        ('1', 'Improvement Required'), ('2', 'Average'),
        ('3', 'Good'), ('4', 'Excellent')],
        string="Attendance")
    time_keeping = fields.Selection([
        ('1', 'Improvement Required'), ('2', 'Average'),
        ('3', 'Good'), ('4', 'Excellent')],
        string="Time Keeping")
    work_relationships = fields.Selection([
        ('1', 'Improvement Required'), ('2', 'Average'),
        ('3', 'Good'), ('4', 'Excellent')],
        string="Work Relationships")


class ProbationReviewTask(models.Model):
    _name = 'probation.review.task'
    _description = 'Probation Review Task'

    review_line_id = fields.Many2one("employee.probation.review.line", string="Probation Review", ondelete="cascade")
    task_objective = fields.Char(string="Objectives Set / Task Given", required=True)
    task_feedback = fields.Char(string="Performance Feedback", required=True)
    task_duration = fields.Char(string="Duration", required=True)


class ProbationReviewImprove(models.Model):
    _name = 'probation.review.improve'
    _description = 'Probation Review Improvement'

    review_line_id = fields.Many2one("employee.probation.review.line", string="Probation Review", ondelete="cascade")
    improve_area = fields.Char(string="Areas for Improvement", required=True)
    improve_discussion = fields.Char(string="Discussion Points / Action Agreed")
    improve_action_by = fields.Char(string="Action by whom", required=True)