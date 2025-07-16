from odoo import fields, models, api, tools, _
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta


class CustomEmployee(models.Model):
    _inherit = 'hr.employee'
    # _rec_name = 'name_extended'

    # name_extended  = fields.Char(string="Name Extended",compute="_compute_name_extended",readonly=True)
    status = fields.Selection(
        [
            ('probation', 'Probation'), 
            ('permanent', 'Permanent Employee'), 
            ('hold', 'Hold'), 
            ('relieve', 'Relieved')
        ],
        string="Status", 
        default='probation',
        groups="hr.group_hr_user"
    )
    is_done = fields.Boolean(string="Is done", default=False,groups="hr.group_hr_user")
    is_probation_extended = fields.Boolean(string="Is Extended Probation", default=False,groups="hr.group_hr_user")
    tt_id = fields.Char(string="TT ID",groups="hr.group_hr_user")

    designation_id = fields.Many2one('hr.employee.designation', string="Designation")
    sub_desination_id = fields.Many2one('hr.employee.sub.designation', string="Sub Designation")
    svn_user_id = fields.Char(string="SVN User ID")
    emp_code = fields.Char(string="Employee Code")

    # permanent address
    permanent_street = fields.Char(string="Permanent Street", groups="hr.group_hr_user")
    permanent_street2 = fields.Char(string="Permanent Street2", groups="hr.group_hr_user")
    permanent_city = fields.Char(string="Permanent City", groups="hr.group_hr_user")
    permanent_state_id = fields.Many2one(
        "res.country.state", string="Permanent State",
        domain="[('country_id', '=?', permanent_country_id)]",
    )
    permanent_zip = fields.Char(string="Permanent Zip", groups="hr.group_hr_user")
    permanent_country_id = fields.Many2one("res.country", string="Permanent Country", groups="hr.group_hr_user")

    # Employee probation review

    review_ids = fields.One2many('hr.employee.probation.review', 'employee_id', string="Reviews")
    promotion_history_ids = fields.One2many('hr.employee.promotion', 'employee_id', string="Promotion History")
    employee_tour_ids = fields.One2many('hr.employee.tour', 'employee_id', string="Tour History")

    # Relative Data

    emergency_contact_relation = fields.Char(string="Contact Relation",groups="hr.group_hr_user")
    emergency_contact_2 = fields.Char(string="Alternate Contact Name",groups="hr.group_hr_user")
    emergency_phone_2 = fields.Char(string="Alternate Contact Phone",groups="hr.group_hr_user")
    emergency_contact_relation_2 = fields.Char(string="Alternate Contact Relation",groups="hr.group_hr_user")

    carrier_start_date = fields.Datetime(string="Career Start Date",groups="hr.group_hr_user")
    joining_date = fields.Date(string="Joining Date", related='contract_id.date_start', groups="hr.group_hr_user")
    relieve_date = fields.Datetime(string="Relieve Date",groups="hr.group_hr_user")

    permanent_employee_date = fields.Date(string="Permanent Employee Date",groups="hr.group_hr_user")
    last_appraisal_date = fields.Date(string="Last Appraisal Date",groups="hr.group_hr_user")

    # Action Methods
    def action_accept(self):
        self.status = 'permanent'
        self.permanent_employee_date = datetime.now()

    def action_extend_probation(self):
        self.is_probation_extended = True

    def action_hold(self):
        self.status = 'hold'

    def action_relieve(self):
        self.status = 'relieve'
        self.contract_id.state = 'cancel'
        self.active = False
        self.relieve_date = datetime.now()

    # Compute Methods
    # def _compute_name_extended(self):
    #     for record in self:
    #         record.name_extended = record.name + "(" + record.department_id.name + ")"

    # def _compute_probation_review_count(self):
    #     for employee in self:
    #         employee.probation_review_count = len(employee.review_ids)

    # ir.cron Methods
    def run_quarterly_appraisal(self):
        today = fields.Date.today()
        appraisal_obj = self.env['hr.appraisal']
        task_obj = self.env['project.task']
        survey_obj = self.env['survey.survey']
        three_months_ago = today - relativedelta(months=3)

        # Get employees eligible for appraisal
        employees = self.search([('active', '=', True), ('status', '=', 'permanent')])
        
        for employee in employees:
            
            # Check if this is the first appraisal (last_appraisal_date is empty)
            if not employee.last_appraisal_date:
                # Use permanent_date for first appraisal
                appraisal_date = employee.permanent_employee_date
            else:
                # Use last_appraisal_date for subsequent appraisals
                appraisal_date = employee.last_appraisal_date

            # Check if 3 months have passed since the last appraisal or permanent date
            next_appraisal_date = appraisal_date + relativedelta(months=3)

            # Check if it's time for a new appraisal (3 months after last appraisal)
            if appraisal_date and today >= next_appraisal_date:
                # Get recent tasks for this employee
                recent_tasks = task_obj.search([
                    ('user_ids', 'in', [employee.user_id.id]),
                    ('date_assign', '>=', three_months_ago),
                    ('date_assign', '<=', today)
                ])
                
                # Get survey for this employee
                manager_survey = survey_obj.search([
                    ('active', '=', True), 
                    ('title', '=', 'SOP Probation Review'),
                ], limit=1)
                
                emp_survey = survey_obj.search([
                    ('active', '=', True), 
                    ('title', '=', 'Burger Quiz'),
                ], limit=1)
                
                # Get unique manager IDs from recent tasks
                manager_ids = recent_tasks.mapped('project_id.user_id.employee_id').ids

                # Create the appraisal record
                appraisal_record = appraisal_obj.create({
                    'employee_id': employee.id,
                    'appraisal_deadline': today + relativedelta(days=1),
                    'hr_manager': True,
                    'hr_manager_ids': [(6, 0, manager_ids)],
                    'hr_emp': True,
                    'manager_survey_id': manager_survey.id,
                    'emp_survey_id': emp_survey.id,
                })

                # hit appraisal action
                appraisal_record.action_start_appraisal()

                # Update the last_appraisal_date to today's date
                employee.last_appraisal_date = today

                # Optional: Log the creation of the appraisal
                self.env['mail.message'].create({
                    'model': 'hr.employee',
                    'res_id': employee.id,
                    'body': f"Quarterly appraisal created for {employee.name} on {today} with {len(manager_ids)} managers",
                    'message_type': 'notification',
                })

    def automatic_probation_review_lines(self):
        task_obj = self.env['project.task']
        survey_obj = self.env['survey.survey']
        
        employees = self.env['hr.employee'].search([
            ('active', '=', True),
            ('status', '=', 'probation'),
            ('joining_date', '!=', False)
        ])
        
        today = fields.Date.today()
        if isinstance(today, datetime):
            today = today.date()

        for employee in employees:
            joining_date = employee.joining_date
            if isinstance(joining_date, datetime):
                joining_date = joining_date.date()
            
            if joining_date > today:
                continue  # Skip if the employee hasn't joined yet

            last_review = employee.review_ids.sorted(lambda r: r.end_date or date.min, reverse=True)[:1]

            if not last_review:
                # First review
                start_date = joining_date
            else:
                # Subsequent review
                last_end_date = last_review.end_date
                if isinstance(last_end_date, datetime):
                    last_end_date = last_end_date.date()
                start_date = last_end_date + relativedelta(days=1)

            # Check if it's time for a new review
            if start_date <= today and len(employee.review_ids) < 12:
                review_end_date = min(start_date + relativedelta(months=1) - relativedelta(days=1), today)

                # Get tasks for this employee from the last month
                one_month_ago = today - relativedelta(months=1)
                recent_tasks = task_obj.search([
                    ('user_ids', 'in', [employee.user_id.id]),
                    ('date_assign', '>=', one_month_ago),
                    ('date_assign', '<=', today)
                ])

                # Get survey for this employee
                manager_survey = survey_obj.search([
                    ('active', '=', True), 
                    ('title', '=', 'SOP Probation Review'),
                ], limit=1)

                # Get unique manager IDs from recent tasks
                manager_ids = recent_tasks.mapped('project_id.user_id').ids

                probation_recod = self.env['hr.employee.probation.review'].create({
                    'employee_id': employee.id,
                    'start_date': start_date,
                    'end_date': review_end_date,
                    'reviewer_ids': [(6, 0, manager_ids)] if manager_ids else [(6, 0, [employee.parent_id.user_id.id])],
                    'review_type': str(len(employee.review_ids) + 1),
                    'review_status': 'sent',
                    'survey_id': manager_survey.id,
                })

                probation_recod.action_send()

        return True

    # Smart Button Functions
    def action_open_probation_reviews(self):
        self.ensure_one()
        return {
            'name': 'Probation Reviews',
            'type': 'ir.actions.act_window',
            'res_model': 'employee.probation.review.line',
            'view_mode': 'tree,form',
            'domain': [('review_id.employee_id', '=', self.id)],
        }

    def action_open_appraisal(self):
        self.ensure_one()
        appraisal_ids = self.env['hr.appraisal'].search([('employee_id', '=', self.id)]).ids
        return {
            'name': 'Appraisal',
            'type': 'ir.actions.act_window',
            'res_model': 'survey.user_input',
            'view_mode': 'tree',
            'domain': [('appraisal_id', 'in', appraisal_ids), ('state', '=', 'done')],
            'context': {'show_appraisal_button': int(1)},
        }


class CustomDesignation(models.Model):
    _inherit = 'hr.job'

    tt_id = fields.Char(string="TT ID")
    current_user_id = fields.Many2one('res.users',string='Opened By')

