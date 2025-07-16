
{
    'name': "Custom Attendance",
    'version': '17.0.1.0.0',
    'summary': """""",
    'author': "Space-o Technology",
    'website': "",
    'company': 'Space-o Technology',
    'maintainer': 'Space-o Technology',
    'category': 'Human Resource',
    'license': 'LGPL-3',
    'depends': ['base','hr_attendance','mail', 'hr_holidays'],
    'data': [
        'data/schedulers.xml',
        'security/ir.model.access.csv',
        'security/attendance_security.xml',
        'views/mail_template.xml',
        'views/attendance_views.xml',
        'wizard/upload_file_wizard_view.xml',
        'views/employee_attendance_report_pivot_view.xml',
        'views/biometric_config.xml',
        # 'views/candidate_call_master_view.xml',
        'views/menus.xml',
    ],
    "assets": {
        'web.assets_backend': [
            'custom_attendance/static/src/js/float_time_second.js',
            'custom_attendance/static/src/xml/float_time_second.xml',
        ],
    },

    'installable': True,
    'auto_install': False,
    'application': True,

}
