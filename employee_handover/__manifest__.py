
{
    'name': "Employee Handover",
    'version': '17.0.1.0.0',
    'summary': """""",
    'author': "Space-o Technology",
    'website': "",
    'company': 'Space-o Technology',
    'maintainer': 'Space-o Technology',
    'category': 'Human Resource',
    'license': 'LGPL-3',
    'depends': ['base','project','web'],
    'data': [
        'data/project_data.xml',
        'security/ir.model.access.csv',
        'security/handover_access_rights.xml',
        # 'view/custom_job_recruitment_view.xml',
        'views/employee_handover_view.xml',
        'report/report_action.xml',
        'report/report_handover_template.xml',
    ],

    'installable': True,
    'auto_install': False,
    'application': True,

}
