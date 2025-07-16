# -*- coding: utf-8 -*-
{
    "name": "custom_survey",
    "summary": "Short (1 phrase/line) summary of the module's purpose",
    "author": "My Company",
    "website": "https://www.yourcompany.com",
    "version": "17.0.0.1",
    # any module necessary for this one to work correctly
    "depends": ["base", "survey","website"],
    # always loaded  

    "data": [
        'security/ir.model.access.csv',
        "views/survey_views.xml",
        # "views/survey_question_view.xml",
        "views/survey_input_print_templates.xml",
        "views/survey_portal_templates.xml",
        "views/survey_question_views.xml",
        "views/survey_survey_views.xml",
        "views/survey_templates.xml",
        "views/survey_user_views.xml",
    ],
    "license": "AGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
}
