/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { CalendarYearRenderer } from "@web/views/calendar/calendar_year/calendar_year_renderer";
const { DateTime } = luxon;

patch(CalendarYearRenderer.prototype, {
    onDayRender(info) {
        if (super.onDayRender) {
            super.onDayRender(info);
        }

        const today = DateTime.now().startOf("day");
        const twoMonthsLater = today.plus({ months: 2 }).endOf("day");
        const currentDate = DateTime.fromJSDate(info.date);

        if (currentDate > twoMonthsLater) {
            info.el.classList.add("o_calendar_disabled");
            info.el.style.opacity = "0.5";
            // info.el.style.cursor = "not-allowed";
        }
    },

    onDateClick(info) {
        const selectedDate = DateTime.fromISO(info.dateStr);
        const today = DateTime.now().startOf("day");
        const twoMonthsLater = today.plus({ months: 2 }).endOf("day");

        if (selectedDate > twoMonthsLater) {
            return; // block clicking after 2 months
        }

        if (super.onDateClick) {
            super.onDateClick(info);
        }
    },

    async onSelect(info) {
        const start = DateTime.fromISO(info.startStr);
        const end = DateTime.fromISO(info.endStr).minus({ days: 1 });

        const today = DateTime.now().startOf("day");
        const twoMonthsLater = today.plus({ months: 2 }).endOf("day");

        if (start > twoMonthsLater || end > twoMonthsLater) {
            return; // block range selection past 2 months
        }

        if (super.onSelect) {
            await super.onSelect(info);
        }
    },
});