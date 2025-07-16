
import uuid
import logging

from odoo import fields, models, api, tools, _
from datetime import datetime, timedelta, time, date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from collections import defaultdict

_logger = logging.getLogger(__name__)


class CustomApplicant(models.Model):
    _name = "hr.applicant"
    _inherit = ["hr.applicant", "mail.tracking.duration.mixin"]

    _track_duration_field = 'stage_id'


    tt_id = fields.Char(string="TT ID")

    # Permanent Address

    permanent_street = fields.Char(string="Permanent Street")
    permanent_street2 = fields.Char(string="Permanent Street2")
    permanent_city = fields.Char(string="Permanent City")
    permanent_state_id = fields.Many2one(
        "res.country.state", string="Permanent State",
        domain="[('country_id', '=?', permanent_country_id)]")
    permanent_zip = fields.Char(string="Permanent Zip")
    permanent_country_id = fields.Many2one("res.country", string="Permanent Country")
    applied_post = fields.Char(string="Post")
    # Current Address

    current_street = fields.Char(string="Current Street")
    current_street2 = fields.Char(string="Current Street2")
    current_city = fields.Char(string="Current City")
    current_state_id = fields.Many2one(
        "res.country.state", string="Current State",
        domain="[('country_id', '=?', current_country_id)]")
    current_zip = fields.Char(string="Current Zip")
    current_country_id = fields.Many2one("res.country", string="Current Country")

    relevant_experience = fields.Char(string="Relevant Experience")
    total_experience = fields.Char(string="Total Experience", compute="_calculate_experience", readonly=True, store=True)
    notice_period = fields.Char(string="Notice Period")
    skype = fields.Char(string="Skype")
    reason_for_change = fields.Char(string="Reason For Change")
    dob = fields.Date(string="Date of Birth")
    marital = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('cohabitant', 'Legal Cohabitant'),
        ('widower', 'Widower'),
        ('divorced', 'Divorced')
    ], string='Marital Status', default='single', tracking=True)

    salary_current = fields.Float("Current Salary", group_operator="avg", help="Current Salary of Applicant",
                                  tracking=True, groups="hr_recruitment.group_hr_recruitment_user")
    salary_current_extra = fields.Char("Current Salary Extra", help="Current Salary by Applicant, extra advantages",
                                       tracking=True, groups="hr_recruitment.group_hr_recruitment_user")

    # Referral Flow

    referral_type = fields.Selection([
        ('current', 'Current Employee'),
        ('ex', 'Ex Employee'),
    ], string='Referral Type', default='current', tracking=True)
    referral_emp_id = fields.Many2one('hr.employee', string="Referral")
    referral_ex_emp_id = fields.Many2one('hr.employee', string="Referral Ex")

    consultancy_name = fields.Char(string="Consultancy Name")
    social_network = fields.Char(string="Social Network")
    google_sheet = fields.Char(string="Google Sheet")
    company = fields.Char(string="Company Name")
    location = fields.Char(string="Location")
    is_same_as_current = fields.Boolean(string="As same as current")

    career_start = fields.Date(string="Career Start")

    # Candidate Data

    family_data_ids = fields.One2many('hr.applicant.family', 'applicant_id', string="Family Details")
    academic_data_ids = fields.One2many('hr.applicant.academic', 'applicant_id', string="Academic Details")
    vendor_id = fields.Many2one('res.partner', string='Vendor', domain=[('customer_rank', '>', 0)])

    # Portal
    token = fields.Char("Portal Token")
    token_expiry = fields.Datetime("Token Expiry Time")
    portal_filled = fields.Boolean("Portal Form Submitted", default=False, tracking=True)
    professional_detail_ids = fields.One2many('hr.applicant.professional.detail', 'applicant_id', string="Professional Details")

    candidate_evaluation_ids = fields.One2many('candidate.evaluation', 'applicant_id', string="Candidate Evaluation")
    evaluation_token = fields.Char("Evaluation Token")
    evaluation_token_expiry = fields.Datetime("Token Expiry")

    @api.depends('career_start')
    def _calculate_experience(self):
        for rec in self:
            if rec.career_start:
                current_date = datetime.today()
                data = relativedelta(current_date, rec.career_start)
                rec.total_experience = f"{data.years} Years {data.months} Months"

    def unlink(self):
        for rec in self:
            # Find the related call record and clear the link
            calls = self.env['hr.applicant.call'].search([('applicant_id', '=', rec.id)])
            if calls:
                calls.write({
                    'applicant_id': False,
                    'is_applicant': False,
                })
        return super(CustomApplicant, self).unlink()

    @api.onchange('is_same_as_current')
    def _map_both_address(self):
        if self.is_same_as_current:
            self.permanent_street = self.current_street if self.current_street else ""
            self.permanent_street2 = self.current_street2 if self.current_street2 else ""
            self.permanent_city = self.current_city if self.current_city else ""
            self.permanent_state_id = self.current_state_id if self.current_state_id else ""
            self.permanent_zip = self.current_zip if self.current_zip else ""
            self.permanent_country_id = self.current_country_id if self.current_country_id else ""


    @api.onchange('stage_id')
    def _send_hire_email(self):
        for rec in self:
            if rec.stage_id.hired_stage:
                candidate_name = rec.name or "Candidate"
                position = rec.job_id.name or "N/A"
                hire_date = rec.date_closed.strftime('%d-%m-%Y') if rec.date_closed else "TBD"

                template = self.env.ref("custom_recruitment.candidate_hired_email_template", raise_if_not_found=False)
                if not template:
                    raise UserError("Email template not found.")
                
                template.send_mail(rec.id, force_send=True)
                

    def _get_employee_create_vals(self):
        self.ensure_one()
        address_id = self.partner_id.address_get(['contact'])['contact']
        address_sudo = self.env['res.partner'].sudo().browse(address_id)
        return {
            'name': self.partner_name or self.partner_id.display_name,
            'work_contact_id': self.partner_id.id,
            'job_id': self.job_id.id,
            'job_title': self.job_id.name,
            'private_street': address_sudo.street,
            'private_street2': address_sudo.street2,
            'private_city': address_sudo.city,
            'private_state_id': address_sudo.state_id.id,
            'private_zip': address_sudo.zip,
            'private_country_id': address_sudo.country_id.id,

            #Permanent address

            'permanent_street': self.permanent_street,
            'permanent_street2': self.permanent_street2,
            'permanent_city': self.permanent_city,
            'permanent_state_id': self.permanent_state_id.id,
            'permanent_zip': self.permanent_zip,
            'permanent_country_id': self.permanent_country_id.id,

            'private_phone': address_sudo.phone,
            'private_email': address_sudo.email,
            'lang': address_sudo.lang,
            'department_id': self.department_id.id,
            'address_id': self.company_id.partner_id.id,
            'work_email': self.department_id.company_id.email or self.email_from,
            # To have a valid email address by default
            'work_phone': self.department_id.company_id.phone,
            'applicant_id': self.ids,
            # 'private_phone': self.partner_phone or self.partner_mobile,
            'birthday': self.dob,
            'marital': self.marital,
        }

    def action_send_portal_link(self):
        _logger.info("Call Function: action_send_portal_link")

        for rec in self:
            # Check if portal already filled
            if rec.portal_filled:
                raise UserError(_("Candidate has already submitted the portal form."))

            # Validate candidate email
            if not rec.email_from:
                raise UserError(_("Candidate email is required to send the portal link."))

            # Generate token and expiry
            token = str(uuid.uuid4())
            expiry = fields.Datetime.now() + timedelta(days=1)

            rec.write({
                'token': token,
                'token_expiry': expiry,
                'portal_filled': False,
            })

            # Build portal URL
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            portal_url = f"{base_url}/candidate/form/{token}"

            _logger.info("Portal URL for %s: %s", rec.name, portal_url)

            # Load email template
            template = self.env.ref("custom_recruitment.candidate_information_email_template")
            if not template:
                raise UserError(_("Email template not found: custom_recruitment.candidate_information_email_template"))

            # Send email with context
            template.with_context(
                portal_url=portal_url,
                user_email=self.env.user.email,
                user_name=self.env.user.name,
                applicant_name=rec.name,
            ).send_mail(
                rec.id,
                email_values={'email_to': rec.email_from},
                force_send=True
            )

            _logger.info("Email sent to candidate: %s", rec.email_from)

    def get_portal_url(self):
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f"{base_url}/candidate/form/{self.token}"

    def send_today_interview_schedule(self):
        tomorrow = date.today() + timedelta(days=1)

        start = datetime.combine(tomorrow, time.min)
        end = datetime.combine(tomorrow, time.max)

        events = self.env['calendar.event'].search([
            ('start', '>=', start),
            ('start', '<=', end),
            ('applicant_id', '!=', False)  # Only those linked to candidates
        ])
        to_email = self.env['ir.config_parameter'].sudo().get_param('custom_recruitment.to_emails_recruitment')
        _logger.info("send_today_interview_schedule --> To Email: %s", to_email)

        email_cc = self.env['ir.config_parameter'].sudo().get_param('custom_recruitment.cc_emails_recruitment')
        _logger.info("send_today_interview_schedule --> Email CC: %s", email_cc)

        if not events:
            return

        rows = ""
        for i, event in enumerate(events, start=1):
            applicant = event.applicant_id
            interviewers = event.applicant_id.interviewer_ids
            interviewer1 = interviewers[0].name if len(interviewers) > 0 else 'NA'
            interviewer2 = interviewers[1].name if len(interviewers) > 1 else 'NA'

            experience = applicant.total_experience if applicant.total_experience else ""

            rows += f"""
            <tr>
                <td>{i}</td>
                <td>{applicant.name}</td>
                <td>{applicant.job_id.name or ''}</td>
                <td>{(event.start + relativedelta(hours=5, minutes=30)).strftime('%I:%M %p')}</td>
                <td>{applicant.source_id.name if applicant.source_id else ''}</td>
                <td>{experience}</td>
                <td>{interviewer1}</td>
                <td>{interviewer2}</td>
                <td><a href="{event.videocall_location or '#'}" target="_blank">{event.videocall_location or '#'}</a></td>
            </tr>
            """

        email_table = f"""
        <table border="1" cellspacing="0" cellpadding="6" style="border-collapse: collapse; width: 100%; font-size: 14px;">
            <thead style="background-color: #F9C74F;">
                <tr>
                    <th>Sr. No</th>
                    <th>Candidate Name</th>
                    <th>Profile</th>
                    <th>Time</th>
                    <th>Source</th>
                    <th>Experience</th>
                    <th>First Interviewer</th>
                    <th>Second Interviewer</th>
                    <th>Interview Link</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        """

        template = self.env.ref('custom_recruitment.candidate_email_template')
        recipient_email = 'interviewer@example.com'

        ctx = {
            'email_table': email_table,
            'user_name': self.env.user.name,
            'user_email': self.env.user.email,
            'formatted_date': tomorrow.strftime('%d %B %Y'),
            'email_to': to_email,
            'email_cc': email_cc,
        }

        dummy_applicant = events[0].applicant_id

        template.with_context(ctx).send_mail(dummy_applicant.id, force_send=True)

    def send_daily_recruitment_summary_email(self):
        today = fields.Date.context_today(self)
        start_dt = datetime.combine(today, datetime.min.time())
        end_dt = datetime.combine(today, datetime.max.time())

        # Offer summary data (past and today)
        offer_sent = self.search([('stage_id.name', '=', 'Contract Proposal'), ('write_date', '>=', start_dt), ('write_date', '<=', end_dt)])
        offer_accepted = self.search([('stage_id.name', '=', 'Contract Signed'), ('write_date', '>=', start_dt), ('write_date', '<=', end_dt)])
        offer_not_accepted = self.search([('active', '=', False), ('write_date', '>=', start_dt), ('write_date', '<=', end_dt)])
        backout = self.search([('stage_id.name', '=', 'Backout'), ('write_date', '>=', start_dt), ('write_date', '<=', end_dt)])

        # Calling summary for today
        calling_applicants = self.env['hr.applicant.call'].search([('create_date', '>=', start_dt), ('create_date', '<=', end_dt)])
        # lineup_applicants = self.env['hr.applicant.call'].search([('create_date', '>=', start_dt), ('create_date', '<=', end_dt), ('status', '=', 'line_up')])

        # Interview Scheduled today (from calendar.event)
        calendar_events = self.env['calendar.event'].search([
            ('create_date', '>=', start_dt),
            ('create_date', '<=', end_dt),
            ('applicant_id', '!=', False)
        ])

        user = self.env.user

        # Prepare Calling and Lined Up Summary grouped by job
        job_summary = defaultdict(lambda: {'calling': 0, 'lineup': 0})
        for rec in calling_applicants:
            job = rec.job_id.name
            job_summary[job]['calling'] += 1
            if rec.status == 'line_up':
                job_summary[job]['lineup'] += 1

        calling_table_rows = ''.join([
            f'<tr><td>{job}</td><td>Calling {vals["calling"]}; Lined up {vals["lineup"]}</td></tr>'
            for job, vals in job_summary.items()
        ]) or '<tr><td colspan="2">No calling or lineup entries today.</td></tr>'

        # Prepare Interview Schedule Summary grouped by source and recruiter
        source_counts = defaultdict(int)
        recruiter_counts = defaultdict(int)
        for ev in calendar_events:
            applicant = ev.applicant_id
            source_counts[applicant.source_id.name] += 1
            recruiter_counts[applicant.user_id.name] += 1

        source_rows = ''.join([
            f'<tr><td>{source}</td><td style="text-align: center;">{count}</td></tr>' for source, count in source_counts.items()
        ]) or '<tr><td colspan="2">No scheduled interviews by source today.</td></tr>'

        recruiter_rows = ''.join([
            f'<tr><td>{recruiter}</td><td style="text-align: center;">{count}</td></tr>' for recruiter, count in recruiter_counts.items()
        ]) or '<tr><td colspan="2">No scheduled interviews by recruiter today.</td></tr>'

        # Compose full HTML table section for template
        table_html_only = f"""
                <h3>Offer Summary</h3>
                <ul>
                    <li>Offer Sent Today: {len(offer_sent)}</li>
                    <li>Offer Accepted Today: {len(offer_accepted)}</li>
                    <li>Offer Not Accepted Today: {len(offer_not_accepted)}</li>
                    <li>Backout Today: {len(backout)}</li>
                </ul>

                <h3>Calling Summary (Job-wise)</h3>
                <table border="1" cellspacing="0" cellpadding="5" style="border-collapse: collapse; width: 100%;">
                    <tr style="background-color: #f2f2f2;"><th>Job Role</th><th>Details</th></tr>
                    {calling_table_rows}
                </table>

                <h3>Scheduled Interviews (Source-wise)</h3>
                <table border="1" cellspacing="0" cellpadding="5" style="border-collapse: collapse; width: 100%;">
                    <tr style="background-color: #f2f2f2;"><th>Source</th><th>Total Scheduled</th></tr>
                    {source_rows}
                </table>

                <h3>Scheduled Interviews (Recruiter-wise)</h3>
                <table border="1" cellspacing="0" cellpadding="5" style="border-collapse: collapse; width: 100%;">
                    <tr style="background-color: #f2f2f2;"><th>Recruiter</th><th>Total Scheduled</th></tr>
                    {recruiter_rows}
                </table>
                """

        # Send using mail.template
        to_email = self.env['ir.config_parameter'].sudo().get_param('custom_recruitment.to_emails_recruitment')
        _logger.info("send_daily_recruitment_summary_email --> To Email: %s", to_email)

        email_cc = self.env['ir.config_parameter'].sudo().get_param('custom_recruitment.cc_emails_recruitment')
        _logger.info("send_daily_recruitment_summary_email --> Email CC: %s", email_cc)

        print("Debug------------------------ to_email ----------------------->", to_email, "email_cc", email_cc)

        dummy_applicant = calendar_events[0].applicant_id if calendar_events else False
        if to_email:
            template = self.env.ref('custom_recruitment.recruitment_summary_email_template')
            template.with_context({
                'summary_date': today.strftime('%d %B %Y'),
                'email_table_html': table_html_only,
                'to_email': to_email,
                'email_cc': email_cc,
                'user_name': user.name,
            }).send_mail(self.id, force_send=True)

    def send_daily_fulfilment_summary_email(self):
        today = fields.Date.context_today(self)
        start_dt = datetime.combine(today, datetime.min.time())
        end_dt = datetime.combine(today, datetime.max.time())

        jobs = self.env['hr.job'].search([])
        calling_ids = self.env['hr.applicant.call'].search([('job_id', 'in', jobs.ids)])

        fulfilment_rows = ""
        total_open = total_closing = total_calling = total_lineup = 0

        for job in jobs:
            applicants = self.search([('job_id', '=', job.id), ('create_date', '>=', start_dt), ('create_date', '<=', end_dt)])
            calling = calling_ids.filtered(lambda a: a.status != 'line_up')
            lineup = calling.filtered(lambda a: a.status == 'line_up')
            closing = applicants.filtered(lambda a: a.stage_id.name == 'Contract Signed')
            offer_notes = '<br/>'.join([f"{a.name}; Exp {a.emp_exp_year} Years; {a.stage_id.name}" for a in applicants if a.stage_id.name != 'Contract Signed']) or '-'
            fulfilment_rows += f"""
                <tr>
                    <td>{job.name}</td>
                    <td>{job.no_of_recruitment}</td>
                    <td>{len(closing)}</td>
                    <td>{len(calling)}</td>
                    <td>{len(lineup)}</td>
                    <td>{offer_notes}</td>
                </tr>
            """
            total_open += job.no_of_recruitment
            total_closing += len(closing)
            total_calling += len(calling)
            total_lineup += len(lineup)

        fulfilment_rows += f"""
            <tr style='font-weight:bold;'>
                <td>Total</td>
                <td>{total_open}</td>
                <td>{total_closing}</td>
                <td>{total_calling}</td>
                <td>{total_lineup}</td>
                <td>-</td>
            </tr>
        """

        to_email = self.env['ir.config_parameter'].sudo().get_param('custom_recruitment.to_emails_upper_management')
        _logger.info("\n\nsend_daily_fulfilment_summary_email --> Email To: %s", to_email)

        email_cc = self.env['ir.config_parameter'].sudo().get_param('custom_recruitment.cc_emails_recruitment')
        _logger.info("\n\nsend_daily_fulfilment_summary_email --> Email CC: %s", email_cc)

        if to_email:
            template = self.env.ref('custom_recruitment.recruitment_fulfilment_email_template')
            template.with_context({
                'fulfilment_date': today.strftime('%d %B %Y'),
                'client_fulfilment_table': fulfilment_rows,
                'to_email': to_email,
                'email_cc': email_cc,
                'user_name': self.env.user.name,
            }).send_mail(self.id, force_send=True)

    def action_send_evaluation_portal_link(self):
        for rec in self:
            base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
            template = self.env.ref("custom_recruitment.email_template_candidate_evaluation")

            # Only send to newly added users
            only_these_users = self.env.context.get('new_user_ids')

            for interviewer in rec.interviewer_ids:
                if only_these_users and interviewer.id not in only_these_users:
                    continue  # Skip already existing ones

                # Generate unique token
                token = str(uuid.uuid4())
                expiry = fields.Datetime.now() + timedelta(days=2)

                # Check if evaluation already exists
                eval_record = self.env["candidate.evaluation"].search(
                    [
                        ("applicant_id", "=", rec.id),
                        ("interviewer_id", "=", interviewer.id),
                    ],
                    limit=1,
                )

                if eval_record and eval_record.token_expiry and eval_record.token_expiry > fields.Datetime.now():
                    continue  # Already has valid token, skip

                if not eval_record:
                    self.env["candidate.evaluation"].create({
                        "applicant_id": rec.id,
                        "interviewer_id": interviewer.id,
                        "token": token,
                        "token_expiry": expiry,
                    })
                else:
                    eval_record.write({
                        "token": token,
                        "token_expiry": expiry,
                    })

                portal_url = f"{base_url}/candidate/evaluation/form/{token}"

                # Send email
                template.with_context(
                    portal_url=portal_url,
                    interviewer_name=interviewer.name,
                    employee_name=rec.name,
                    expiry_date=expiry,
                    user_email=self.env.user.email,
                    user_name=self.env.user.name,
                ).send_mail(
                    rec.id,
                    email_values={"email_to": interviewer.email},
                    force_send=True,
                )



class CandidateFamilyMaster(models.Model):
    _name = 'hr.applicant.family'
    _description = "Candidate's Family Data"

    applicant_id = fields.Many2one('hr.applicant', string="Candidate")
    tt_id = fields.Char(string="TT ID")
    name = fields.Char(string="Name")
    relation = fields.Char(string="Relation")
    occupation = fields.Char(string="Occupation")


class CandidateAcademicMaster(models.Model):
    _name = 'hr.applicant.academic'
    _description = "Candidate's Academic Data"

    applicant_id = fields.Many2one('hr.applicant', string="Candidate")
    type_id = fields.Many2one('hr.recruitment.degree', string="Degree")
    tt_id = fields.Char(string="TT ID")
    institute_name = fields.Char(string=" Institute Name")
    pass_year = fields.Char(string="Pass Year")
    percentage = fields.Char(string="Percentage/Grade")


class ProfessionalDetail(models.Model):
    _name = 'hr.applicant.professional.detail'
    _description = 'Candidate Professional Details'

    company_name = fields.Char(string='Company Name', required=True)
    designation = fields.Char(string='Designation', required=True)
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    reason = fields.Text(string='Reason for Leaving')
    current_ctc = fields.Float(string='Current CTC (Monthly)')
    expected_ctc = fields.Float(string='Expected CTC (Monthly)')
    notice_period = fields.Char(string='Notice Period')
    last_appraisal_date = fields.Date(string='Last Appraisal Date')
    applicant_id = fields.Many2one('hr.applicant', string='Candidate')


class CandidateEvaluation(models.Model):
    _name = 'candidate.evaluation'
    _description = 'Candidate Evaluation Form'

    applicant_id = fields.Many2one('hr.applicant', string="Candidate")
    interviewer_id = fields.Many2one('res.users', string="Interviewer")
    
    # Rating fields (1 to 5)
    understanding_position = fields.Selection([(str(i), str(i)) for i in range(1, 6)], string="Understanding of Position")
    technical_skill = fields.Selection([(str(i), str(i)) for i in range(1, 6)], string="Technical Skill Set")
    logical_skill = fields.Selection([(str(i), str(i)) for i in range(1, 6)], string="Logical Thinking Skill Set")
    communication_skill = fields.Selection([(str(i), str(i)) for i in range(1, 6)], string="Interpersonal/Communication Skill Set")
    organizational_fit = fields.Selection([(str(i), str(i)) for i in range(1, 6)], string="Organizational Fit")
    attitude = fields.Selection([(str(i), str(i)) for i in range(1, 6)], string="Attitude")
    work_culture_fit = fields.Selection([(str(i), str(i)) for i in range(1, 6)], string="Work-culture Fit")
    new_learning = fields.Selection([(str(i), str(i)) for i in range(1, 6)], string="New Learning")
    
    # Technologies and ratings
    tech_1 = fields.Char(string="Technology 1")
    tech_1_rating = fields.Selection([(str(i), str(i)) for i in range(1, 6)], string="Tech 1 Rating")
    tech_2 = fields.Char(string="Technology 2")
    tech_2_rating = fields.Selection([(str(i), str(i)) for i in range(1, 6)], string="Tech 2 Rating")
    tech_3 = fields.Char(string="Technology 3")
    tech_3_rating = fields.Selection([(str(i), str(i)) for i in range(1, 6)], string="Tech 3 Rating")

    good_points = fields.Text(string="Good Points")
    improvement_points = fields.Text(string="Improvement Points")

    recommendation = fields.Selection([
        ('draft', 'Draft'),
        ('hire', 'Hire'),
        ('no_hire', 'Do Not Hire'),
        ('hold', 'Hold'),
        ('practical_assignment', 'Practical Assignment'),
    ], string="Recommendation", default="draft")

    # Portal
    token = fields.Char(string="Access Token", readonly=True)
    token_expiry = fields.Datetime(string="Token Expiry")
    is_filled = fields.Boolean(string="Form Filled", default=False)
    is_not_prectical = fields.Boolean(string="Without Practical Evaluation", default=False)

    # Practical Assignment

    task_duration = fields.Char(string="Task Duration")
    task_actual_duration = fields.Char(string="Task Actual Duration")
    task_achievement = fields.Char(string="Task Achievement")
    quality_of_work = fields.Selection([(str(i), str(i)) for i in range(1, 6)], string="Quality of Work")

    task_attachment = fields.Binary(string="Task Attachment", attachment=True)

    good_points_pr = fields.Text(string="Project Good Points")
    improvement_points_pr = fields.Text(string="Project Improvement Points")
    recommendation_pr = fields.Selection([
        ('draft', 'Draft'),
        ('hire', 'Hire'),
        ('reject', 'Rejected'),
        ('future', 'Future Reference'),
    ], string="Project Recommendation", default="draft")

    practical_completed = fields.Boolean(string="Practical Evaluation Completed", default=False)
