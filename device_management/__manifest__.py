{
    'name': 'Device Management',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Manage company devices and their assignments',
    'description': """
        Device Management module for managing company devices:
        * Track devices and their assignments
        * QR code based device check-in/check-out
        * Device history tracking
    """,
    'author': 'Space-O Technologies',
    'depends': ['base', 'custom_employee', 'mail', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/device_management_views.xml',
        'views/device_line_view.xml',
        'views/device_category_views.xml',
        'views/hr_employee_view.xml',
        'data/device_category_data.xml',
        'data/device_schedulers.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'sequence': 1,
    'assets': {
        'web.assets_backend': [
            # 'device_management/static/src/scss/device_dashboard.scss',
            'device_management/static/src/components/**/*.js',
            'device_management/static/src/components/**/*.xml',
            'device_management/static/src/components/**/*.scss',
        ],
    },
} 