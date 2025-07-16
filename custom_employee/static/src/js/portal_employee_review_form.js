/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";


publicWidget.registry.EmployeeReviewWidget = publicWidget.Widget.extend({
    selector: '#emp-review-form',

    events: {
        'click #add-task-row': '_onAddTaskRow',
        'click .remove-task': '_onRemoveTaskRow',
    },

    start() {
        this.taskIndex = parseInt(this.$el.find('#task-count').val()) || 1;
        this.taskNewIndex = parseInt(this.$el.find('#task-new-count').val()) || 1;
        return this._super(...arguments);
    },

    _onAddTaskRow(ev) {
        ev.preventDefault();
        const $card = $(ev.currentTarget).closest('.employee-review-card');
        const section = $card.data('section');

        if (section === 'task') {
            const $container = $card.find('#task-container');
            const newRow = $(`
                <div class="row task-row mb-3">
                    <div class="col-md-4 mb-2">
                        <input type="text" name="task_objective_${this.taskIndex}" class="form-control" placeholder="Objectives Set / Task Given" required="required"/>
                    </div>
                    <div class="col-md-4 mb-2">
                        <input type="text" name="task_feedback_${this.taskIndex}" class="form-control" placeholder="Performance Feedback" required="required"/>
                    </div>
                    <div class="col-md-3 mb-2">
                        <input type="text" name="task_duration_${this.taskIndex}" class="form-control" placeholder="Duration" required="required"/>
                    </div>
                    <div class="col-md-1 mb-2">
                        <button type="button" class="btn btn-danger remove-task w-100"><i class="fa fa-trash" aria-hidden="true"></i></button>
                    </div>
                </div>
            `);
            $container.find('.task-row').last().after(newRow);
            this.taskIndex++;
            $container.find('#task-count').val(this.taskIndex);
        }

        if (section === 'improve') {
            const $container = $card.find('#task-new-container');
            const newRow = $(`
                <div class="row task-row mb-3">
                <hr/>
                    <div class="col-md-6 mb-2">
                        <input type="text" name="improve_area_${this.taskNewIndex}" class="form-control" placeholder="Enter area" required="required"/>
                    </div>
                    <div class="col-md-6 mb-2">
                        <input type="text" name="improve_discussion_${this.taskNewIndex}" class="form-control" placeholder="Enter discussion/action"/>
                    </div>
                    <div class="col-md-6 mb-2">
                        <input type="text" name="improve_action_by_${this.taskNewIndex}" class="form-control" placeholder="e.g., Employee" required="required"/>
                    </div>
                    <div class="col-md-1 mb-2">
                        <button type="button" class="btn btn-danger remove-task w-100"><i class="fa fa-trash" aria-hidden="true"></i></button>
                    </div>

                </div>

            `);
            $container.find('.task-row').last().after(newRow);
            this.taskNewIndex++;
            $container.find('#task-new-count').val(this.taskNewIndex);
        }
    },

    _onRemoveTaskRow(ev) {
        ev.preventDefault();
        const $card = $(ev.currentTarget).closest('.employee-review-card');
        const $rows = $card.find('.task-row');
        if ($rows.length > 1) {
            $(ev.currentTarget).closest('.task-row').remove();
        }
    },
});
