
{
    'name': "Custom Employee",
    'version': '17.0.1.0.0',
    'summary': """""",
    'author': "Space-o Technology",
    'website': "",
    'company': 'Space-o Technology',
    'maintainer': 'Space-o Technology',
    'category': 'Human Resource',
    'license': 'LGPL-3',
    'depends': ['base','hr','hr_contract','hr_hourly_cost', 'project','custom_recruitment','website'],
    'data': [
        'data/scheduler.xml',
        'data/probation_review_template.xml',
        'security/ir.model.access.csv',
        # 'view/custom_survey_view.xml',
        'view/custom_contract_view.xml',
        'view/hr_designation_view.xml',
        'view/res_users_view.xml',
        'view/templates.xml',
        'view/dynamic_document_template_view.xml',
        'view/probation_review_portal_template.xml',
        'view/probation_review_views.xml',
        'view/custom_employee_view.xml',
        'wizard/document_selection_wizard_view.xml',
    ],

    'assets': {
        'web.assets_frontend': [
            'custom_employee/static/src/js/portal_employee_review_form.js',
        ],
    },

    'installable': True,
    'auto_install': False,
    'application': True,

}
