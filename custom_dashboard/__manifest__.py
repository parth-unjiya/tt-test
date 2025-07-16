# -*- coding: utf-8 -*-
{
    "name": "custom_dashboard",
    "summary": "Short (1 phrase/line) summary of the module's purpose",
    "author": "My Company",
    "website": "https://www.yourcompany.com",
    "category": "Uncategorized",
    "version": "17.0.0.1",
    "license": 'LGPL-3',
    "depends": ["base", "hr", "hr_timesheet", "hr_attendance", "hr_holidays", "project","employee_handover","odoo_website_helpdesk"],
    # always loaded
    "data": [
        # 'security/ir.model.access.csv',
        "security/dashboard_security.xml",
        "views/menu.xml",
    ],
    "assets": {
        "web.assets_backend": {
            "/custom_dashboard/static/src/component/*/*.js",
            "/custom_dashboard/static/src/component/*/*.xml",
            # "/custom_dashboard/static/src/component/*/*.scss",
            # "/custom_dashboard/static/src/component/*/*.css",
        },
    },
}
