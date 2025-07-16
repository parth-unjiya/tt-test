/** @odoo-module **/

// import { _t } from "@web/core/l10n/translation";
import options from "@web_editor/js/editor/snippets.options";
console.log('options', options);

options.registry.PolicyCards = options.Class.extend({
    start() {
        var self = this;
        console.log('policy cards started');
        return this._super.apply(this, arguments).then(function () {
            self.updateUI();
        });
    },

    updateUI() {
        const grid = this.$target.find('.policy-grid');
        const list = this.$target.find('.policy-list');
        const displayMode = this.$target.data('display_mode') || 'grid'; // Default display mode

        if (displayMode === 'list') {
            grid.hide(); // Hide grid view
            list.show(); // Show list view
        } else {
            grid.show(); // Show grid view
            list.hide(); // Hide list view
        }

        this.fetchPolicies().then(policies => {
            this.renderPolicies(policies);
        });
    },

    renderPolicies(policies) {
        const grid = this.$target.find('.policy-grid');
        const list = this.$target.find('.policy-list');
        
        grid.empty(); // Clear existing cards
        list.empty(); // Clear existing list items

        // Get customization options
        const bgColor = this.$target.data('bg_color') || '#1a1a1a'; // Default color
        const buttonBgColor = this.$target.data('button_bg_color') || '#a4c23b'; // Default button color

        policies.forEach(policy => {
            // Create card for grid view
            const policyCard = `<div class="policy-card" data-category-id="${policy.sop_category_id}" style="background: ${bgColor};">
                <div class="card-content">
                    <span class="version-chip">v${policy.version}</span>
                    <h4>${policy.name}</h4>
                    <span>Effective From: ${policy.effective_date}</span>
                    <a href="/hr_policy/${policy.id}" class="view-policy-btn" style="background: ${buttonBgColor};">View Policy</a>
                </div>
            </div>`;
            grid.append(policyCard);

            // Create item for list view
            const policyItem = `<div class="policy-item" style="padding: 1rem; border-bottom: 1px solid #ccc;">
                <h4>${policy.name}</h4>
                <span>Effective From: ${policy.effective_date}</span>
                <a href="/hr_policy/${policy.id}" class="view-policy-btn" style="background: ${buttonBgColor};">View Policy</a>
            </div>`;
            list.append(policyItem);
        });
    },

    _onDisplayModeChange: function (ev) {
        const selectedMode = ev.target.value;
        const grid = this.$target.find('.policy-grid');
        const list = this.$target.find('.policy-list');

        if (selectedMode === 'list') {
            grid.hide(); // Hide grid view
            list.show(); // Show list view
        } else {
            grid.show(); // Show grid view
            list.hide(); // Hide list view
        }
    },

    _setupEventListeners: function () {
        const displayModeSelect = this.$target.find('[data-attribute-name="display_mode"]');
        displayModeSelect.on('change', this._onDisplayModeChange.bind(this));
    },

    onBuilt() {
        this._super(...arguments);
        this.updateUI();
    },

    cleanForSave() {
        this._super(...arguments);
        this.updateUI();
    },

    onRemove() {
        this.$target.find('.policy-grid').empty(); // Clear the grid
    },
});

export default {
    PolicyCards: options.registry.PolicyCards,
}; 