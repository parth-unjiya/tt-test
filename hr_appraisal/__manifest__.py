# -*- coding: utf-8 -*-
{
    "name": "HRMS Employee Appraisal",
    "version": "17.0.1.0.0",
    "category": "Human Resources",
    "summary": """Roll out appraisal plans and get the best of your 
    workforce""",
    "description": """This app is a powerful and versatile tool that can help 
    organizations improve their employee appraisal process and boost employee 
    performance.""",
    "author": "Space-O Technology",
    "company": "Space-O Technology",
    "maintainer": "Space-O Technology",
    "depends": ["hr", "custom_dashboard"],
    "data": [
        "data/hr_appraisal_stages_demo.xml",
        "data/appraisal_email_template.xml",
        "security/oh_appraisal_groups.xml",
        "security/hr_appraisal_security.xml",
        "security/ir.model.access.csv",
        "views/appraisal_templates.xml",
        "views/hr_appraisal_views.xml",
        "views/hr_appraisal_stages_view.xml",
        "views/appraisal_data_points_views.xml",
        "views/templates.xml",
        "views/menuitems.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "hr_appraisal/static/src/js/appraisal_form.js",
        ],
    },
    "images": ["static/description/banner.jpg"],
    "license": "AGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
}
