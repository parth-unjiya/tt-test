# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    web_title = fields.Char(
        "Web Title",
        help="Setup Title Name,which replace Odoo",
        default="Space-O",
        config_parameter="web_title",
    )

    landing_pages_url = fields.Char(
        "Landing Pages URL",   
        help="Setup Landing Pages URL",
        default="/web/login",
        config_parameter="landing_pages_url",
    )

    app_show_footer = fields.Boolean(
        "Show Footer",
        help="When enable,User can see Footer",
        config_parameter="app_show_footer",
    )

    header_social_links = fields.Boolean(
        "Show Header Social Links",   
        help="When enable,User can see Social Links",
        config_parameter="header_social_links",
    )

    header_call_to_action = fields.Boolean(
        "Show Header Contact Us Button",
        help="When enable,User can see Call To Action",
        config_parameter="header_call_to_action",
    )

    header_text_element = fields.Boolean(
        "Show Header Text",
        help="When enable,User can see Header Text",
        config_parameter="header_text_element",
    )

    header_search_box = fields.Boolean(
        "Show Header Search Box",
        help="When enable,User can see Search Box",
        config_parameter="header_search_box",
    )

    cc_emails = fields.Char(
        string="Default CC Emails",
        config_parameter="odoo_comman_app.cc_emails",
        help="Comma-separated list of CC emails (e.g., hr1@example.com, hr2@example.com)"
    )

    cc_templates = fields.Many2many(
        'mail.template',
        string="Email Templates for CC",
        help="Select the email templates for which CC should be automatically added."
    )

    to_emails = fields.Char(
        string="Default To Emails",
        config_parameter="odoo_comman_app.to_emails",
        help="Comma-separated list of To emails (e.g., management@example.com, director@example.com)"
    )

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        
        # Save the selected template IDs in ir.config_parameter
        template_ids = self.cc_templates.ids
        self.env['ir.config_parameter'].sudo().set_param(
            'odoo_comman_app.cc_templates',
            ','.join(map(str, template_ids))
        )

    # Override the get_values method to load the configuration values
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        
        # Load the template IDs from ir.config_parameter and set it to the field
        template_ids = self.env['ir.config_parameter'].sudo().get_param(
            'odoo_comman_app.cc_templates', ''
        )
        if template_ids:
            res['cc_templates'] = [(6, 0, list(map(int, template_ids.split(','))))]

        return res