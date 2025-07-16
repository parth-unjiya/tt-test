/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const { Component } = owl;

class HrPolicySystray extends Component {
    
    setup() {
        this.action = useService("action");
    }

    openWebsitePage() {
        const domainUrl = window.location.origin;
        const pageUrl = `${domainUrl}/hr_policy`;
        window.location.href = pageUrl;
        // window.open(pageUrl, "");
    }
}

HrPolicySystray.template = 'hr_policy.HrPolicySystray';

registry.category("systray").add("hr_policy.HrPolicy", {
    Component: HrPolicySystray,
}, { sequence: 110 });
