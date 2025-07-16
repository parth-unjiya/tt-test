/** @odoo-module **/

import { registry } from "@web/core/registry";

// Unregister unwanted menu items
registry.category("user_menuitems").remove("documentation");
registry.category("user_menuitems").remove("support");
registry.category("user_menuitems").remove("odoo_account");
