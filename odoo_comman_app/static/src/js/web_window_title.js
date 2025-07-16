/** @odoo-module alias=web.window.title **/

import { WebClient } from "@web/webclient/webclient";
import { patch } from "@web/core/utils/patch";
import { session } from "@web/session";

patch(WebClient.prototype, {
    setup() {
        var self = this;
        super.setup();
        const web_title = session.web_title || 'Space-O';
        this.title.setParts({ zopenerp: web_title });

    }
});

