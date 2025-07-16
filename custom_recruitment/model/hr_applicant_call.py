import datetime

from odoo import fields, models, api, tools, _
from datetime import datetime, date
from dateutil import relativedelta
from odoo.exceptions import UserError, ValidationError

import mysql.connector
import logging

_logger = logging.getLogger(__name__)


class CandidateCallMaster(models.Model):
    _name = 'hr.applicant.call'
    _description = "Applicant Call Data"
    _inherit = ['mail.thread.cc',
                'mail.thread.main.attachment',
                'mail.thread.blacklist',
                'mail.thread.phone',
                'mail.activity.mixin',
                'utm.mixin']
    _mailing_enabled = True
    _primary_email = 'email'

    job_id = fields.Many2one('hr.job', string="Role",tracking=True)
    source_id = fields.Many2one('utm.source', string="Source")
    consultancy_name = fields.Char(string="Consultancy Name")
    name = fields.Char(string="Candidate Name", required=True, tracking=True)
    email = fields.Char(string="Candidate Email", required=True, tracking=True)
    mobile = fields.Char(string="Candidate Mobile", required=True, tracking=True)
    company = fields.Char(string="Company Name", required=True, tracking=True)
    location = fields.Char(string="Location")
    social_network = fields.Char(string="Social Network")
    google_sheet = fields.Char(string="Google Sheet")
    comments = fields.Text(string="Comments")
    calling_time = fields.Datetime(string="Calling Time")
    career_start = fields.Date(string="Career Start")
    reason_for_change = fields.Char(string="Reason For Change", tracking=True)
    notice_period = fields.Char(string="Notice Period", tracking=True)
    relevant_experience = fields.Char(string="Relevant Experience")
    total_experience = fields.Char(string="Total Experience",compute='_calculate_experience',readonly=True)
    current_ctc = fields.Char(string="Current CTC", tracking=True)
    expected_ctc = fields.Char(string="Expected CTC")
    linkedin = fields.Char(string="Linkedin")
    career_start_year = fields.Char(string="Career Start Year")
    applied_post = fields.Char(string="Post", tracking=True)

    referral_emp_id = fields.Many2one('hr.employee', string="Referral", tracking=True)
    applicant_id = fields.Many2one('hr.applicant', string="Candidate")
    applicant_stage_id = fields.Many2one(related='applicant_id.stage_id', string="Candidate Status")

    is_applicant = fields.Boolean(string="Is transferred in candidate")
    tt_id = fields.Char(string="TT ID")

    status = fields.Selection(
        [
            ('new', 'New'),
            ('not_interested', 'Not Interested'),
            ('ringing', 'Ringing/Not Answering'),
            ('followup', 'Follow Up/Call Back'),
            ('send_mail', 'Send Email'),
            ('future', 'Future Reference'),
            ('line_up', 'Line Up'),
        ], 
        string="Status",
        default='new',
        tracking=True
    )

    @api.depends('career_start')
    def _calculate_experience(self):
        for record in self:
            if record.career_start:
                current_date = datetime.today()
                data = relativedelta.relativedelta(current_date, record.career_start)
                record.total_experience = f"{data.years} Years {data.months} Months"
            else:
                record.total_experience = ""

    def action_application(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Candidate Application',
            'res_model': 'hr.applicant',
            'view_mode': 'form',
            'res_id': self.applicant_id.id
        }

    def reset(self):
        self.status = 'new'

    def convert_to_application(self):
        for rec in self:
            try:
                vals = {
                    'name': rec._get_application_name(),
                    'partner_name': rec.name or "",
                    'email_from': rec.email or "",
                    'partner_mobile': rec.mobile or "",
                    'consultancy_name': rec.consultancy_name or "",
                    'job_id': rec.job_id.id if rec.job_id else False,
                    'source_id': rec.source_id.id if rec.source_id else False,
                    'career_start': rec.career_start,
                    'company': rec.company or "",
                    'location': rec.location or "",
                    'social_network': rec.social_network or "",
                    'google_sheet': rec.google_sheet or "",
                    'reason_for_change': rec.reason_for_change or "",
                    'notice_period': rec.notice_period or "",
                    'relevant_experience': rec.relevant_experience or "",
                    'total_experience': rec.total_experience or "",
                    'linkedin_profile': rec.linkedin or "",
                }
                applicant_id = rec.env['hr.applicant'].create(vals)
                rec.write({
                    'is_applicant': True,
                    'applicant_id': applicant_id.id,
                    'status': 'line_up'
                })
            except Exception as e:
                raise UserError(_("Error while converting to application:\n\n%s") % e)

    def _get_application_name(self):
        """Generate application name"""
        if self.name and self.job_id:
            return f"{self.name}'s Application for {self.job_id.name}"
        elif self.name:
            return "New Application"
        else:
            return ""

    def copy(self):
        raise ValidationError(_("Cannot copy this record"))

    @api.onchange('career_start')
    def _onchange_career_start(self):
        if self.career_start and self.career_start > date.today():
            raise UserError(_("Career start date cannot be in the future"))

    _sql_constraints = [
        ('unique_email_mobile', 'unique(email, mobile)', 'Candidate email and mobile number must be unique.!'),
    ]

    def unlink(self):
        for rec in self:
            if rec.applicant_id:
                raise UserError("Cannot delete call record with a linked applicant. Please delete the applicant first.")
        return super().unlink()


    # Temprory Code For Update Create Date
    def run_dynamic_create_date_sync(self, mysql_config, mysql_table, mysql_id_field, mysql_date_field, odoo_model, odoo_sql_table, config_key, batch_size=1000):
        _logger.info(f"🔄 Starting sync for: {mysql_table} → {odoo_model}")

        # mysql_config = {
        #     "host": "localhost",
        #     "user": "root",
        #     "password": "ur48x",
        #     "database": "tt_db_v1_p",
        # }        

        try:
            mysql_conn = mysql.connector.connect(**mysql_config)
            mysql_cursor = mysql_conn.cursor(dictionary=True)

            last_id = int(
                self.env["ir.config_parameter"].sudo().get_param(config_key) or 0
            )

            # Prepare dynamic SQL
            query = f"""
                SELECT {mysql_id_field} AS id, {mysql_date_field} AS created_at
                FROM {mysql_table}
                WHERE {mysql_id_field} > %s AND {mysql_date_field} IS NOT NULL
                ORDER BY {mysql_id_field} ASC
            """
            mysql_cursor.execute(query, (last_id,))
            rows = mysql_cursor.fetchall()

            if not rows:
                _logger.info(f"✅ No new records to sync for {odoo_model}")
                return

            max_id = last_id
            updated_count = 0

            for row in rows:
                tt_id = str(row["id"])
                timestamp = row["created_at"]

                try:
                    create_date = datetime.fromtimestamp(int(timestamp))
                except Exception as e:
                    _logger.warning(f"⚠️ Invalid timestamp for TT ID {tt_id}: {timestamp}")
                    continue

                record = self.env[odoo_model].sudo().search([("tt_id", "=", tt_id)], limit=1)

                _logger.info(f"Process record ::::::::::::::::::: {tt_id}")

                if record:
                    self.env.cr.execute(f"""
                        UPDATE {odoo_sql_table}
                        SET create_date = %s
                        WHERE id = %s
                    """, (create_date.strftime("%Y-%m-%d %H:%M:%S"), record.id))
                    updated_count += 1

                max_id = max(max_id, int(tt_id))

            self.env["ir.config_parameter"].sudo().set_param(config_key, str(max_id))
            _logger.info(f"✅ Updated {updated_count} records in {odoo_model} (Next ID > {max_id})")

            mysql_cursor.close()
            mysql_conn.close()

        except Exception as e:
            _logger.error(f"❌ Sync failed for {mysql_table}: {e}")