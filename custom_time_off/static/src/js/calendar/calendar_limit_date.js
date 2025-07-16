/** @odoo-module **/

import { CalendarController } from "@web/views/calendar/calendar_controller";
import { FormViewDialog } from "@web/views/view_dialogs/form_view_dialog";
import { _t } from "@web/core/l10n/translation";
import { calendarView } from "@web/views/calendar/calendar_view";
import { registry } from "@web/core/registry";

const { DateTime } = luxon;


export class LimitedCalendarController extends CalendarController {

   
    // get dateRange() {
    //     const today = luxon.DateTime.now();  // Get the current DateTime
    //     const twoMonthsLater = today.plus({ months: 2 });  // Calculate 2 months later
    //     return { min: today, max: twoMonthsLater };  // Return DateTime objects
    // }

    // get datePickerProps() {
    //     const { min, max } = this.dateRange;  // Get the DateTime objects
    //     return {
    //         ...this.options,
    //         minDate: min,  // Pass the DateTime object, not an ISO string
    //         maxDate: max,  // Pass the DateTime object, not an ISO string
    //     };
    // }


   /**
    * Check if a date is within the next 2 months from today.
    * @param {Date | string} rawDate
    */
   isDateWithinLimit(rawDate) {
       if (!rawDate) return false;

       let date;
       try {
           date = rawDate instanceof Date
               ? DateTime.fromJSDate(rawDate)
               : DateTime.fromISO(rawDate.toString());
       } catch (error) {
           return false;
       }

       const now = DateTime.now().startOf("day");
       const max = now.plus({ months: 2 }).endOf("day");
       return date <= max;
   }

   /**
    * Handle creation of calendar events.
    */
   async createRecord(record) {
       const startDate = record.start || record.date_start || null;

       if (!this.isDateWithinLimit(startDate)) {
           this.env.services.notification.add(
               _t("You cannot create an event beyond 2 months from today."),
               { type: "warning" }
           );
           return;
       }

       return super.createRecord(record);
   }


   /**
    * Allow editing if event is in the past 10 days (including today)
    * OR within the next 2 months.
    */
   async editRecord(record, context = {}, shouldFetchFormViewId = true) {

       const startDate = record.start || record.date_start || null;

       if (!startDate) {
           this.env.services.notification.add(
               _t("Invalid event date."),
               { type: "warning" }
           );
           return;
       }

       let date;
       try {
           date = startDate instanceof Date
               ? DateTime.fromJSDate(startDate)
               : DateTime.fromISO(startDate.toString());
       } catch (error) {
           this.env.services.notification.add(
               _t("Invalid date format."),
               { type: "warning" }
           );
           return;
       }

       const today = DateTime.now().startOf("day");
       const min = today.minus({ days: 5 });
       const max = today.plus({ months: 2 }).endOf("day");

       if (date < min || date > max) {
           this.env.services.notification.add(
               _t("You can only edit events from the last 5 days or up to 2 months ahead."),
               { type: "warning" }
           );
           return;
       }

       return super.editRecord(record, context, shouldFetchFormViewId);
   }


}


const customCalendarView = {
    ...calendarView,
    Controller: LimitedCalendarController,
};

registry.category("views").add("calendar_limit_date", customCalendarView);
// time_off_calendar_dashboard