/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

publicWidget.registry.AppraisalReviewForm = publicWidget.Widget.extend({
    selector: '.appraisal_review_form',
    events: {
        'click .o_appraisal_submit': '_onSubmitForm',

        'click #addGoal': '_onAddGoalRow',
        'click #removeGoal': '_onRemoveGoalRow',

        'click #addGoalFuture': '_onAddFutureGoalRow',
        'click #removeGoalFuture': '_onRemoveFutureGoalRow',

        'click #addGoalNotes': '_onAddGoalClick',
        'click .btn-remove-goal': '_onRemoveGoalClick',
    },

    init() {
        this._super(...arguments);
        this.goalIndex = 2; // Start from index 2 since first row is static
    },

    start() {
        console.log('Appraisal Review Form initialized');
        return this._super.apply(this, arguments);
    },

    // ========== Goal Row Management ==========
   _onAddGoalRow: function (ev) {
        ev.preventDefault();

        const $table = this.$el.find('#last-goals-table tbody');
        const $lastRow = $table.find('.last-goal-entry').last();
        const $newRow = $lastRow.clone(true, true);

        // Calculate next index based on row count
        const nextIndex = $table.find('.last-goal-entry').length + 1;

        // Update inputs and select fields
        $newRow.find('input, select').each(function () {
            const $elem = $(this);
            const nameAttr = $elem.attr('name') || '';
            const parts = nameAttr.split('_');
            parts.pop();  // remove the last index
            const baseName = parts.join('_');
            const newName = baseName + '_' + nextIndex;

            $elem.val('');
            $elem.attr('id', newName);
            $elem.attr('name', newName);
        });

        // Add remove event
        $newRow.find('.remove-goal').on('click', function () {
            $(this).closest('tr').remove();
        });

        $table.append($newRow);
    },


    _onRemoveGoalRow: function(ev) {
        ev.preventDefault();
        const $rows = this.$el.find('.last-goal-entry');
        if ($rows.length > 1) {
            $rows.last().remove();
        }
    },

    _onAddFutureGoalRow: function (ev) {
        ev.preventDefault();

        const $table = this.$el.find('#goals-table tbody');
        const $lastRow = $table.find('.goal-entry').last();
        const $newRow = $lastRow.clone(true, true);
        console.log("-----------------newRow-----------------",$newRow);


        // Calculate next index based on row count
        const nextIndex = $table.find('.goal-entry').length + 1;

        // Update inputs and select fields
        $newRow.find('input').each(function () {
            const $elem = $(this);
            const nameAttr = $elem.attr('name') || '';
            console.log("nameAttr-----------------",nameAttr);
            const parts = nameAttr.split('_');
            parts.pop();  // remove the last index
            const baseName = parts.join('_');
            const newName = baseName + '_' + nextIndex;
            console.log("newName-----------------",newName);

            $elem.val('');
            $elem.attr('id', newName);
            $elem.attr('name', newName);
        });
        console.log("newRow-----------------",$newRow);

        // Add remove event
        $newRow.find('.remove-goal-future').on('click', function () {
            $(this).closest('tr').remove();
        });

        $table.append($newRow);
    },


    _onRemoveFutureGoalRow: function(ev) {
        ev.preventDefault();
        const $rows = this.$el.find('.goal-entry');
        if ($rows.length > 1) {
            $rows.last().remove();
        }
    },

    // ========== Form Submission ==========
    _onSubmitForm: async function(ev) {
        ev.preventDefault();
        this._clearErrors();

        if (!this._validateForm()) {
            console.log('Validation failed');
            return;
        }

        const formData = {
            goals: this._getGoalsData(),
            ratings: {
                communication: this.$el.find('[name="rating_communication"]').val(),
                // Add other ratings
            },
            comments: {
                employee: this.$el.find('#employee_comments').val(),
                evaluator: this.$el.find('#evaluator_comments').val(),
            }
        };

        try {
            const response = await jsonrpc('/appraisal/submit', { data: formData });
            if (response.success) {
                window.location.href = '/appraisal/thankyou';
            } else {
                console.error('Submission failed:', response.error);
            }
        } catch (error) {
            console.error('Error:', error);
        }
    },

    // ========== Validation ==========
    _validateForm: function() {
        let isValid = true;
        // Validate Goals
        this.$el.find('.last-goal-entry').each((index, row) => {
            const $row = $(row);
            if (!$row.find('[name^="goal_description"]').val().trim()) {
                this._showError($row.find('[name^="goal_description"]'), 'Goal description is required');
                isValid = false;
            }
        });

        // Validate Ratings (example)
        const communicationRating = this.$el.find('[name="rating_communication"]').val();
        if (!communicationRating || communicationRating < 1 || communicationRating > 10) {
            this._showError(this.$el.find('[name="rating_communication"]'), 'Invalid rating');
            isValid = false;
        }

        return isValid;
    },

    _showError: function($input, message) {
        $input.addClass('is-invalid');
        $input.after(`<div class="form-error-msg text-danger mt-1">${message}</div>`);
    },

    _clearErrors: function() {
        this.$el.find('.is-invalid').removeClass('is-invalid');
        this.$el.find('.form-error-msg').remove();
    },

    // ========== Data Serialization ==========
    _getGoalsData: function() {
        const goals = [];
        this.$el.find('.last-goal-entry').each(function() {
            goals.push({
                description: $(this).find('[name^="goal_description"]').val(),
                action: $(this).find('[name^="goal_action"]').val(),
                completed: $(this).find('[name^="goal_completed"]').val(),
            });
        });
        return goals;
    },


    _onAddGoalClick: function () {
        const $tableBody = this.$('#goals-notes-table tbody');
        const index = $tableBody.find('tr').length + 1;

        const $newRow = $(`
            <tr class="goal-entry">
                <td><input type="text" name="goal_${index}" class="form-control" required="required"/></td>
                <td><input type="text" name="goal_notes_${index}" class="form-control" required="required"/></td>
                <td>
                    <button type="button" class="btn btn-danger btn-remove-goal">
                        <i class="fa fa-trash"></i>
                    </button>
                </td>
            </tr>
        `);
        $tableBody.append($newRow);
    },

    _onRemoveGoalClick: function (ev) {
        $(ev.currentTarget).closest('tr').remove();
    },
});