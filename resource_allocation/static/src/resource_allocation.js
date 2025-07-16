/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { CalendarController } from "@web/views/calendar/calendar_controller";
import { CalendarModel } from '@web/views/calendar/calendar_model';
import { AllocationCalendarFilterPanel } from "./calendar_filter_panel";
import { calendarView } from "@web/views/calendar/calendar_view";
import { ControlPanel } from "@web/search/control_panel/control_panel";

import { registry } from "@web/core/registry";


export class ResourceAllocationCalendarController extends CalendarController {
    static props = ["*"];
    static components = {
        ...ResourceAllocationCalendarController.components,
        FilterPanel: AllocationCalendarFilterPanel,
    };
    setup() {
        super.setup(...arguments);
    }
}

export class AllocationControlPanel extends ControlPanel { }

export class AllocationCalendarModel extends CalendarModel {

    setup() {
        super.setup(...arguments);
    }

    
    /**
     * Override normalizeRecord and set isTimeHidden to false
     * @override
     */
    normalizeRecord(rawRecord) {
        const result = super.normalizeRecord(rawRecord);
        result.isTimeHidden = false;
        result.isAllDay = true;
        result.isHatched = true;
        return result;
    }
    
    addFilterFields(record, filterInfo) {
        
        if (filterInfo.fieldName == 'resource_id') {
            return {
                colorIndex: record.rawRecord.resource_type == 'material' ? record.rawRecord['color'] : '',
                resourceType: record.rawRecord['resource_type'],

            };
        }
        return {
            ...super.addFilterFields(record, filterInfo),
            resourceType: record.rawRecord['resource_type'],
        };
    }

    makeFilterDynamic(filterInfo, previousFilter, fieldName, rawFilter, rawColors) {
        return {
            ...super.makeFilterDynamic(filterInfo, previousFilter, fieldName, rawFilter, rawColors),
            resourceType: rawFilter['resourceType'],
            colorIndex: rawFilter['colorIndex'],
        };
    }

}

export const AllocationCalendarView = {
    ...calendarView,
    Controller: ResourceAllocationCalendarController,
    ControlPanel: AllocationControlPanel,
    Model: AllocationCalendarModel,
};
registry.category("views").add("allocation_calendar", AllocationCalendarView);
