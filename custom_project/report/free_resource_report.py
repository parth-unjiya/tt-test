from odoo import models, tools, fields, api


class FreeResourceReport(models.Model):
    _name = "free.resource.report"
    _description = "Free Resource Report"
    _auto = False

    resource_id = fields.Many2one('resource.resource', string="Resource")
    allocation_count = fields.Integer(string="Allocation Count")
    allocated_hours = fields.Float(string="Allocated Hours")
    available_hours = fields.Float(string="Available Hours")
    date = fields.Date(string="Date")
    department_id = fields.Many2one('hr.department', string="Department")


    def _select(self):
        return """
            MIN(r.id + (EXTRACT(EPOCH FROM gs.day)::int)) AS id,
            r.id AS resource_id,
            d.id AS department_id,
            COUNT(ra.id) AS allocation_count,
            COALESCE(SUM(ra.allocation_hours), 0.0) AS allocated_hours,
            8.0 - COALESCE(SUM(ra.allocation_hours), 0.0) AS available_hours,
            gs.day::date AS date
        """

    def _from(self):
        return """
            resource_resource r
            LEFT JOIN hr_employee e ON e.resource_id = r.id
            LEFT JOIN hr_department d ON d.id = e.department_id
            CROSS JOIN generate_series(
               (CURRENT_DATE - INTERVAL '30 days')::date,
               (CURRENT_DATE + INTERVAL '30 days')::date,
               interval '1 day'
            ) AS gs(day)
            LEFT JOIN resource_allocation ra
               ON ra.resource_id = r.id
               AND gs.day BETWEEN ra.start_date AND ra.end_date
           """

    def _where(self):
        return "TRUE"

    def _group_by(self):
        return "r.id, d.id, gs.day"

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
               CREATE VIEW %s AS
               SELECT %s
                 FROM %s
                WHERE %s
             GROUP BY %s
           """ % (
            self._table,
            self._select(),
            self._from(),
            self._where(),
            self._group_by()
        ))