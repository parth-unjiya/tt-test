# -*- coding: utf-8 -*-
from odoo import models, fields, tools, api


from odoo import models, tools, fields


class AllocateResourceReport(models.Model):
    _name = "allocate.resource.report"
    _description = "Allocated Resource Report"
    _auto = False

    project_id = fields.Many2one('project.project', string="Project")
    task_id = fields.Many2one('project.task', string="Task")
    resource_id = fields.Many2one('resource.resource', string="Resource")
    user_id = fields.Many2one('res.users', string="User")
    department_id = fields.Many2one('hr.department', string="Department")
    allocation_hours = fields.Float(string="Allocated Hours")
    hours_per_day = fields.Float(string="Hours Per Day")
    date = fields.Date(string="Date")

    def _select(self):
        return """
            MIN(ra.id + (EXTRACT(EPOCH FROM gs.day)::int)) AS id,
            ra.project_id,
            ra.task_id,
            ra.resource_id,
            ra.user_id,
            d.id AS department_id,
            COALESCE(ra.hours_per_day::float, 0.0) AS hours_per_day,
            gs.day::date AS date,
            COALESCE(
                CASE WHEN ra.hours_per_day IS NOT NULL THEN ra.hours_per_day::float ELSE 0 END,
                0
            ) AS allocation_hours
        """

    def _from(self):
        return """
            resource_allocation ra
            JOIN resource_resource r ON r.id = ra.resource_id
            LEFT JOIN hr_employee hr ON hr.resource_id = r.id
            LEFT JOIN hr_department d ON d.id = hr.department_id
            CROSS JOIN LATERAL (
                SELECT day::date
                FROM generate_series(
                    date_trunc('month', CURRENT_DATE)::date,
                    (date_trunc('month', CURRENT_DATE) + INTERVAL '1 month - 1 day')::date,
                    interval '1 day'
                ) day
                WHERE EXTRACT(DOW FROM day) BETWEEN 1 AND 5  -- Monday (1) to Friday (5)
                   OR EXISTS (
                       SELECT 1 FROM hr_leave_mandatory_day m
                       WHERE m.start_date = day::date
                       AND (m.company_id IS NULL OR m.company_id = r.company_id)
                   )
            ) AS gs(day)
        """

    def _where(self):
        return """
            ra.state = 'approve'
            AND ra.start_date IS NOT NULL
            AND ra.end_date IS NOT NULL
            AND gs.day BETWEEN ra.start_date::date AND ra.end_date::date
        """

    def _group_by(self):
        return """
            ra.project_id,
            ra.task_id,
            ra.resource_id,
            ra.user_id,
            d.id,
            ra.hours_per_day,
            gs.day
        """

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT {self._select()}
                FROM {self._from()}
                WHERE {self._where()}
                GROUP BY {self._group_by()}
            )
        """)
