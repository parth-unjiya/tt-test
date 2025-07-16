/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { ProjectTaskStateSelection } from "@project/components/project_task_state_selection/project_task_state_selection";

patch(ProjectTaskStateSelection.prototype, {    
    setup() {
        // Call original setup
        super.setup();

        // Remove "03_approved" from icons, colors, buttons
        delete this.icons["03_approved"];
        delete this.colorIcons["03_approved"];
        delete this.colorButton["03_approved"];

        // Remove "02_changes_requested" from icons, colors, buttons
        delete this.icons["02_changes_requested"];
        delete this.colorIcons["02_changes_requested"];
        delete this.colorButton["02_changes_requested"];
    },

    get options() {
        const labels = new Map(super.options);
        const states = ["1_canceled", "1_done"];
        const currentState = this.props.record.data[this.props.name];
        if (currentState !== "04_waiting_normal") {
            states.unshift("01_in_progress");  // "02_changes_requested" "03_approved" removed
        }
        return states.map((state) => [state, labels.get(state)]);
    }
});
