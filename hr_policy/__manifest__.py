# -*- coding: utf-8 -*-
{
    "name": "HR Policy",
    "summary": "Manage HR Policies.",
    "author": "My Company",
    "website": "https://www.yourcompany.com",
    "version": "17.0.0.1",
    "depends": ["base", "mail", "website", "web", "web_editor"],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "views/website_menu_views.xml",
        "data/website_menu_data.xml",
        "views/hr_policy.xml",
        'views/sop_category.xml',
        'views/hr_policy_template.xml',
        'views/snippets.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'hr_policy/static/src/js/policy.js',
            'hr_policy/static/src/css/policy.css',

        ],
        "web.assets_backend": [
            "hr_policy/static/src/js/icon_policy.js",
            "hr_policy/static/src/js/icon_policy.xml",
        ],
        'website.assets_wysiwyg': [
            'hr_policy/static/src/js/snippets.js',
        ],
    },
    "license": "LGPL-3",
}
