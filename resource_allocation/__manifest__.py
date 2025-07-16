{
    "name": "Resource Allocation",
    "version": "17.0.1.0.0",
    "summary": """""",
    "author": "Space-o Technology",
    "website": "",
    "company": "Space-o Technology",
    "maintainer": "Space-o Technology",
    "category": "Services",
    "license": "LGPL-3",
    "depends": ["base", "project", "resource", "hr","custom_dashboard","custom_project"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/resource_availability_wizard_view.xml",
        "views/project_task_view.xml",
        "views/resource_allocation_views.xml",
        "views/resource_action.xml",
        "report/free_resource_report_view.xml",
        "views/menus.xml",

    ],
    'assets': {
        'web.assets_backend': [
            'resource_allocation/static/src/calendar_filter_panel.js',
            'resource_allocation/static/src/calendar_filter_panel.xml',
            'resource_allocation/static/src/calendar_filter_panel.scss',
            'resource_allocation/static/src/resource_allocation.js',
        ],
    },

    "installable": True,
    "auto_install": False,
    "application": True,
}
