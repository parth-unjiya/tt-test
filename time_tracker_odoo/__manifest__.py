# -*- coding: utf-8 -*-
{
    "name": "time_tracker_odoo",
    "summary": "Short (1 phrase/line) summary of the module's purpose",
    "author": "My Company",
    "website": "https://www.yourcompany.com",
    "category": "Uncategorized",
    "version": "17.0.0.1",
    "license": 'LGPL-3',
    # any module necessary for this one to work correctly
    "depends": ["base"],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "views/auth_api_key.xml",
        "views/mail_template.xml",
        "views/capture_data_views.xml",
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
