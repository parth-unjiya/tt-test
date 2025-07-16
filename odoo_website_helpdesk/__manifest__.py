# -*- coding: utf-8 -*-
{
    'name': "Website Helpdesk Support Ticket Management",
    'version': '17.0.1.0.1',
    'category': 'Website',
    'summary': """The website allows for the creation of tickets, which can 
    then be controlled from the backend. Furthermore, a bill that includes 
    the service charge can be generated for the ticket for odoo community 
    Edition version 17.""",
    'description': """A ticket can be created from the website and subsequently
     managed from the backend. Additionally, a bill can be generated for the
     ticket, which includes the service cost.""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    # remove -> 'project', 'sale_project', 'hr_timesheet'
    'depends': ['website','mail', 'contacts'],
    'data': [
        'security/odoo_website_helpdesk_groups.xml',
        'security/odoo_website_helpdesk_security.xml',
        'security/ir.model.access.csv',
        'data/helpdesk_category_data.xml',
        'data/helpdesk_replay_template_data.xml',
        'data/helpdesk_type_data.xml',
        'data/ir_cron_data.xml',
        'data/ir_sequence_data.xml',
        'data/mail_template_data.xml',
        'data/ticket_stage_data.xml',
        'views/helpdesk_category_views.xml',
        'views/helpdesk_tag_views.xml',
        'views/helpdesk_type_views.xml',
        # 'views/fetchmail_view.xml',
        'views/merge_ticket_views.xml',
        'views/odoo_website_helpdesk_portal_templates.xml',
        'views/portal_templates.xml',
        'views/rating_form.xml',
        'report/helpdesk_ticket_report_template.xml',
        'views/res_config_settings_views.xml',
        'views/team_helpdesk_views.xml',
        'views/ticket_helpdesk_views.xml',
        'views/ticket_stage_views.xml',
        'views/ticket_cancel_reason_view.xml',
        # 'views/website_form.xml',
        'views/helpdesk_views.xml',
        'views/mail_compose_message_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'odoo_website_helpdesk/static/src/js/ticket_details.js',
            '/odoo_website_helpdesk/static/src/js/portal_search.js',
            # '/odoo_website_helpdesk/static/src/js/multiple_product_choose.js',
        ],
        'web.assets_backend': [
            'odoo_website_helpdesk/static/src/xml/chatter.xml',
        ]
    },
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
