/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class ApprovalNotificationClientAction extends Component {
    setup() {
        console.log("ApprovalNotificationClientAction---------------->setup");
        this.notification = useService("notification");
        this.busService = useService("bus_service");

        // Start listening to notifications
        this.busService.addEventListener("notification", this._onNotification.bind(this));
        this.busService.startPolling();
    }

    _onNotification(notifications) {
        for (const [channel, message] of notifications) {
            if (channel.startsWith("res.users.")) {
                if (message.type === "notification" && message.title === "Approval Notification") {
                    this.notification.add(message.message, {
                        title: message.title,
                        type: 'info',
                        sticky: message.sticky || false,
                    });
                }
            }
        }
    }
}

ApprovalNotificationClientAction.template = "ApprovalNotificationClientAction";
registry.category("actions").add("approval_notification_action", ApprovalNotificationClientAction);

export default ApprovalNotificationClientAction;