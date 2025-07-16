# -*- coding: utf-8 -*-
import uuid
import inflect

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta, datetime


class HrAppraisal(models.Model):
    """Create the model Appraisal"""
    _name = 'hr.appraisal'
    _inherit = 'mail.thread'
    _rec_name = 'employee_id'
    _description = 'HR Appraisal'


    @api.model
    def _read_group_stage_ids(self, categories, domain, order):
        """ Read all the stages and display it in the kanban view,
        even if it is empty."""
        category_ids = categories._search([], order=order,
                                          access_rights_uid=SUPERUSER_ID)
        return categories.browse(category_ids)

    def _default_stage_id(self):
        """Setting default stage"""
        rec = self.env['hr.appraisal.stages'].search([], limit=1,
                                                     order='sequence ASC')
        return rec.id if rec else None


    employee_id = fields.Many2one('hr.employee', string="Employee",
                                  help="Employee name")
    appraisal_deadline = fields.Date(string="Appraisal Deadline", required=True,
                                     help="Deadline date of the appraisal")
    final_interview = fields.Date(string="Final Interview",
                                  help="After sending survey link,you can"
                                       " schedule final interview date")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id,
                                 help="Company name of the current record")
    hr_manager = fields.Boolean(string="Manager", default=False,
                                help="Whether the manager needs to "
                                     "attend survey")
    hr_emp = fields.Boolean(string="Is Employee", default=False,
                            help="Whether the employee needs to attend survey")
    hr_collaborator = fields.Boolean(string="Evaluator", default=False,
                                     help="To mention collaborators for"
                                          " the survey")
    hr_colleague = fields.Boolean(string="Technical Evaluator", default=False,
                                  help="To mention colleagues for the survey")
    hr_manager_id = fields.Many2one('hr.employee',
                                    string="Select Manager",
                                    help="Managers to attend survey")
    hr_colleague_id = fields.Many2one('hr.employee',
                                      string="Select Technical Evaluator",
                                      help="Colleagues to attend survey")
    hr_collaborator_id = fields.Many2one('hr.employee',
                                         string="Select Evaluator",
                                         help="Collaborators to review")
    final_evaluation = fields.Text(string="Final Evaluation",
                                   help="Final evaluation after the appraisal")
    app_period_from = fields.Datetime(string="From", required=True,
                                      readonly=True,
                                      default=fields.Datetime.now(),
                                      help="From Date")
    tot_comp_survey = fields.Integer(string="Count Answers",
                                     compute="_compute_completed_survey",
                                     help="Number of Answers")
    creater_id = fields.Many2one('res.users', string="Created By",
                                 default=lambda self: self.env.uid,
                                 help="User created appraisal")
    stage_id = fields.Many2one('hr.appraisal.stages', string='Stage',
                               index=True,
                               default=lambda self: self._default_stage_id(),
                               group_expand='_read_group_stage_ids',
                               help="Stage of the appraisal")
    color = fields.Integer(string="Color Index", help="Color of the stage")

    check_sent = fields.Boolean(string="Check Sent Mail", copy=False,
                                help="Will be true when the appraisal started")
    check_draft = fields.Boolean(string="Check Draft", default=True, copy=False,
                                 help="Will be true when the appraisal in "
                                      "draft state")
    check_cancel = fields.Boolean(string="Check Cancel", copy=False,
                                  help="Will be true when the appraisal is "
                                       "canceled")
    check_done = fields.Boolean(string="Check Done", copy=False,
                                help="Will be true when the appraisal is done")

    # Add Weightage fields
    manager_total_weightage = fields.Integer(string="Manager Weightage", )
    manager_weightage_count = fields.Float(string="Manager Weightage Count", compute="_compute_weightage_counts")
    manager_total_score = fields.Float(string="Manager Score")

    employee_total_weightage = fields.Integer(string="Employee Weightage", )
    employee_weightage_count = fields.Float(string="Employee Weightage Count", compute="_compute_weightage_counts")
    employee_total_score = fields.Float(string="Employee Score")

    collaborator_total_weightage = fields.Integer(string="Evaluator Weightage", )
    collaborator_weightage_count = fields.Float(string="Evaluator Weightage Count", compute="_compute_weightage_counts")
    collaborator_total_score = fields.Float(string="Evaluator Score")

    colleague_total_weightage = fields.Integer(string="Technical Evaluator Weightage", )
    colleague_weightage_count = fields.Float(string="Technical Evaluator Weightage Count", compute="_compute_weightage_counts")
    colleague_total_score = fields.Float(string="Technical Evaluator Score")

    total_weightage_score = fields.Float(string="Employee Total Weightage Score")

    token = fields.Char("Portal Token")
    token_expiry = fields.Datetime("Token Expiry Time")


    @api.onchange('manager_total_weightage', 'employee_total_weightage', 'collaborator_total_weightage', 'colleague_total_weightage')
    def _compute_total_weightage_score(self):
        print("Computing Total Weightage Score")
        for record in self:
            # Summing up weightages, treating None as 0
            total_weightage = sum([
                record.manager_total_weightage or 0,
                record.employee_total_weightage or 0,
                record.collaborator_total_weightage or 0,
                record.colleague_total_weightage or 0
            ])

            if total_weightage > 100:
                raise ValidationError("Total Weightage must be less than or equal to 100.")

            # Assign the computed total weightage to a field if needed.
            # For example, if you have a field named 'total_weightage_score'
            # record.total_weightage_score = total_weightage



    @api.constrains('hr_manager', 'hr_emp', 'hr_collaborator', 'hr_colleague')
    def _check_weightage_values(self):
        field_role_map = {
            'manager_total_weightage': ('hr_manager', "Manager"),
            # 'employee_total_weightage': ('hr_emp', "Employee"),
            'collaborator_total_weightage': ('hr_collaborator', "Collaborator"),
            'colleague_total_weightage': ('hr_colleague', "Colleague")
        }

        for record in self:
            for field, (role_field, role_name) in field_role_map.items():
                if getattr(record, field) <= 0 and getattr(record, role_field):
                    raise ValidationError(f"{role_name} Weightage must be greater than 0.")

    @api.depends('hr_manager_id', 'manager_total_weightage', 'hr_collaborator_id', 'collaborator_total_weightage', 'hr_colleague_id',
                 'colleague_total_weightage', 'employee_total_weightage')
    def _compute_weightage_counts(self):
        for record in self:
            # Calculate counts for each group only if the respective boolean field is active
            manager_count = len(record.hr_manager_ids) if record.hr_manager else 0
            collaborator_count = len(record.hr_collaborator_ids) if record.hr_collaborator else 0
            colleague_count = len(record.hr_colleague_ids) if record.hr_colleague else 0

            # Avoid division by zero by setting counts to 0 if no active managers/collaborators/colleagues
            record.manager_weightage_count = (record.manager_total_weightage / manager_count) if manager_count > 0 else 0
            record.employee_weightage_count = record.employee_total_weightage if record.hr_emp else 0
            record.collaborator_weightage_count = (record.collaborator_total_weightage / collaborator_count) if collaborator_count > 0 else 0
            record.colleague_weightage_count = (record.colleague_total_weightage / colleague_count) if colleague_count > 0 else 0

    @api.constrains('appraisal_deadline')
    def _check_appraisal_deadline(self):
        """Method _check_appraisal_deadline to check whether the appraisal
        deadline given is in the past"""
        if self.appraisal_deadline <= fields.date.today() or self.appraisal_deadline == fields.date.today:
            raise ValidationError(_("Appraisal deadline needs "
                                    "to be greater than today"))

    def action_done(self):
        """Method action_done to make the appraisal into done state"""
        rec = self.env['hr.appraisal.stages'].search([('sequence', '=', 3)])
        self.stage_id = rec.id
        self.check_done = True
        self.check_draft = False

    def action_set_draft(self):
        """Method action_set_draft to make the appraisal into draft state"""
        rec = self.env['hr.appraisal.stages'].search([('sequence', '=', 1)])
        self.stage_id = rec.id
        self.check_draft = True
        self.check_sent = False

    def action_cancel(self):
        """Method action_cancel to make the appraisal into canceled state"""
        rec = self.env['hr.appraisal.stages'].search([('sequence', '=', 4)])
        self.stage_id = rec.id
        self.check_cancel = True
        self.check_draft = False

    
    def action_start_appraisal(self):
        """Start appraisal and send emails to employee and reviewers."""
        token = str(uuid.uuid4())
        baseurl = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        expiry = fields.Datetime.now() + timedelta(days=1)

        self.write({'token': token, 'token_expiry': expiry})

        token_url = f"{baseurl}/appraisal/review_form/{token}"
        review_date = f"{inflect.engine().ordinal(15)} {datetime.today().strftime('%B %Y')}"

        reviewers = [
            (self.employee_id, 'employee'),
            *[(p, 'reviewer') for p in self.hr_manager_id + self.hr_collaborator_id + self.hr_colleague_id],
        ]

        for partner, role in reviewers:
            self._send_appraisal_email(
                partner=partner,
                role=role,
                token_url=token_url,
                review_date=review_date,
                expiry=expiry,
            )

        stage = self.env['hr.appraisal.stages'].search([('sequence', '=', 2)], limit=1)
        if stage:
            self.write({'stage_id': stage.id, 'check_sent': True, 'check_draft': False})


    def _send_appraisal_email(self, partner, role, token_url, review_date, expiry):
        """Send appraisal email using the appropriate QWeb template."""
        template_xmlid = {
            'employee': 'hr_appraisal.appraisal_template_employee',
            'reviewer': 'hr_appraisal.appraisal_template_reviewer',
        }.get(role)

        if not template_xmlid:
            raise UserError(_('Invalid role "%s"') % role)

        template = self.env.ref(template_xmlid, raise_if_not_found=False)
        if not template:
            raise UserError(_('Template "%s" not found') % template_xmlid)

        context = {
            'token_url': token_url,
            'review_date': review_date,
            'token_expiry': expiry.strftime('%B %d, %Y at %I:%M %p'),
            'recipient_name': partner.name,
            'sender_name': self.env.user.name,
            'sender_email': self.env.user.email,
        }

        template.with_context(context).send_mail(self.id, force_send=True)

    def action_get_answers(self):
        """ This function will return all the answers posted related to
        this appraisal."""

        return {
            'model': 'ir.actions.act_window',
            'name': 'Answers',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'hr.appraisal.data',
            'domain': [('appraisal_id', '=', self.id)],
        }

    def _compute_completed_survey(self):
        """Method _compute_completed_survey will compute the completed survey"""
        for rec in self:
            answers = self.env['hr.appraisal.data'].search(
                [('appraisal_id', '=', rec.id)])
            rec.tot_comp_survey = len(answers)
