from odoo import models, fields, api, _


class ReleaseNotes(models.Model):
    _name = "release.note"
    _description = "Release Notes"

    tt_id = fields.Char(string="TT ID")
    plateform = fields.Selection(
        [("ios", "iOS"), ("android", "Android"), ("web", "Web")],
        default="ios",
        string="Plateform",
    )
    app_version = fields.Char(string="Application Version")
    build_number = fields.Char(string="Build Number")
    commit_id = fields.Char(string="SVN Number / Commit ID")
    project_id = fields.Many2one("project.project", string="Project")
    milestone_id = fields.Many2one("project.milestone", string="Milestone")
    released_date = fields.Datetime(string="Released Date")

    tested_device = fields.Text(string="Tested Device")
    application_link = fields.Char(string="Application Link")

    steps_to_install = fields.Html(string="Steps To Install")

    features_implemented = fields.Html(string="Features Implemented")
    test_cases = fields.Html(string="Test Cases")
    open_bugs_status = fields.Html(string="Open Bugs Status")
    fixed_bugs_status = fields.Html(string="Fixed Bugs Status")

    notes = fields.Html(string="Notes")
    known_issues = fields.Html(string="Known Issues")
    pending_modules = fields.Html(string="Pending Modules")

    build_remark = fields.Char(string="Build Remark")

    verified_by = fields.Many2one("res.users", string="Verified By")

    def action_verify_by_current_user(self):
        for rec in self:
            rec.verified_by = self.env.user
