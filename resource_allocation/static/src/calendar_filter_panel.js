/** @odoo-module **/

import { CalendarFilterPanel } from "@web/views/calendar/filter_panel/calendar_filter_panel";

export class AllocationCalendarFilterPanel extends CalendarFilterPanel { 
    static props = ["*"];

    getNoColor(filter) {
        return this.section.fieldName == 'resource_id' ? 'no_filter_color' : '';
    }
}

AllocationCalendarFilterPanel.subTemplates = {
    filter: "resource_allocation.AllocationCalendar.filter",
};