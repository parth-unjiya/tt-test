# -*- coding: utf-8 -*-
{
    "name": "Comman App",
    "version": "17.0.0.1",
    "author": "Space-O",
    "category": "Base",
    "website": "https://www.spaceotechnologies.com/",
    "license": "LGPL-3",
    "sequence": 2,
    "summary": "Odoo app for common customizations across projects.",
    "depends": ["base", "base_setup", "web", "website"],
    "data": [
        "data/website_data.xml",
        "views/odoo_comman_customize_views.xml",
        "views/website_views.xml",
        "views/website_template.xml",
        "views/res_config_settings.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "odoo_comman_app/static/src/js/web_window_title.js",
            "odoo_comman_app/static/src/js/menus.js",
        ],
    },
    "installable": True,
    "application": True,
    "auto_install": True,
    # ================= Descriptions ===================
    "description": """
        Comman App For Odoo
        ===================
        1. Replaces "Odoo" in Windows title.
        2. Remove Powered by Odoo.
        3. Set Website Logo.
        4. Hide HeaderEliments Like[Text, SearchBox, Number, Contectus Button].
        5. Remove Website Footer Brand Promotion.
        6. Hide Website Menu Items.
        7. Add Logo Redirect Url On Website logo.
        8. Hide and Show website Footer Base on configuration.
        9. Hide and Show Header Eliments Base on configuration.
    """,
}
