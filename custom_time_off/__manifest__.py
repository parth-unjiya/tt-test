
{
    'name': "Custom Time Off",
    'version': '17.0.1.0.0',
    'summary': """""",
    'author': "Space-o Technology",
    'website': "",
    'company': 'Space-o Technology',
    'maintainer': 'Space-o Technology',
    'category': 'Human Resource',
    'license': 'LGPL-3',
    'depends': ['base','hr_holidays'],
    'data': [
        'data/time_off_type_data.xml',
        'security/ir.model.access.csv',
        'views/holidays_view.xml',
        'views/hr_sandwich_leave_rule.xml',
        'views/hr_leave_type_view.xml',
        # 'views/candidate_call_master_view.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'custom_time_off/static/src/js/calendar/calendar_year_renderer.js',
            'custom_time_off/static/src/js/calendar/calendar.scss',
        ],
    },

    'installable': True,
    'auto_install': False,
    'application': True,

}
