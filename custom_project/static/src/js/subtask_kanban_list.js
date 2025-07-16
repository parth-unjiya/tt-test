/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ProjectTaskKanbanRecord } from "@project/views/project_task_kanban/project_task_kanban_record";

patch(ProjectTaskKanbanRecord.prototype, {
    setup() {
        // Call original setup
        super.setup();

        // Override default folded state
        this.state.folded = false;
    },
});
