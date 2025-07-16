/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useInputField } from "@web/views/fields/input_field_hook";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import { useNumpadDecimal } from "@web/views/fields/numpad_decimal_hook";
import { Component } from "@odoo/owl";

/**
 * Convert float hours into HH:MM:SS format
 */
function formatFloatTimeSeconds(value) {
    if (typeof value !== "number") return "00:00:00";

    const totalSeconds = Math.round(value * 3600);
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;

    return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

/**
 * Convert HH:MM:SS string into float hours
 */
function parseFloatTimeSeconds(value) {
    let sign = 1;
    if (value.startsWith("-")) {
        value = value.slice(1);
        sign = -1;
    }
    const values = value.split(":");
    if (values.length > 3) {
        throw new Error(`"${value}" is not a correct time format`);
    }

    const hours = parseInt(values[0]) || 0;
    const minutes = parseInt(values[1]) || 0;
    const seconds = parseInt(values[2]) || 0;

    return sign * (hours + minutes / 60 + seconds / 3600);
}

export class FloatTimeSecondField extends Component {
    static template = "web.FloatTimeSecondField";
    static props = {
        ...standardFieldProps,
        inputType: { type: String, optional: true },
        placeholder: { type: String, optional: true },
    };
    static defaultProps = {
        inputType: "text",
    };

    setup() {
        useInputField({
            getValue: () => this.formattedValue,
            refName: "numpadDecimal",
            parse: (v) => parseFloatTimeSeconds(v),
        });
        useNumpadDecimal();
    }

    get formattedValue() {
        const value = this.props.record.data[this.props.name] || 0;
        return formatFloatTimeSeconds(value);
    }
}

export const floatTimeSecondField = {
    component: FloatTimeSecondField,
    displayName: _t("Time with Seconds"),
    supportedOptions: [
        {
            label: _t("Type"),
            name: "type",
            type: "string",
            default: "text",
        },
    ],
    supportedTypes: ["float"],
    isEmpty: () => false,
    extractProps: ({ attrs, options }) => ({
        inputType: options.type,
        placeholder: attrs.placeholder,
    }),
};

registry.category("fields").add("float_time_second", floatTimeSecondField);
