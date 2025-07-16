/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";

class DeviceDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            devices: [],
            stats: {
                total: 0,
                available: 0,
                occupied: 0,
                byDepartment: {},
                byOS: {},
                byDeviceType: {},
                recentActivities: []
            },
            filter: 'all',
            isLoading: true,
        });
        this.loadData();
    }

    async loadData() {
        try {
            // Fetching main data from 'device.management'
            const data = await this.orm.searchRead(
                "device.management",
                [["state", "!=", "not_working"],
                ["state", "!=", "sold"],
                ["state", "!=", "spare"]],
                [
                    "name", "device_label", "os_version", "is_occupied",
                    "occupied_by", "department_id", "state", "device_type","device_line_ids"
                ]
            );

            if (data && data.length > 0) {
                // Collect all device_line_ids from the fetched data
                const deviceLineIds = data.flatMap(record => record.device_line_ids);

                if (deviceLineIds.length > 0) {
                    // Fetching related 'device.list' data
                    const deviceLineData = await this.orm.searchRead(
                        "device.line",
                        [["id", "in", deviceLineIds]],
                        [
                            "id", "device_id", "device_label",
                            "device_type", "is_occupied", "occupied_by",
                            "occupied_at", "released_at", "status"
                        ]
                    );
                    deviceLineData.forEach(line => {
                        if (line.occupied_at) {
                            const date = new Date(line.occupied_at);
                            date.setHours(date.getHours() + 5);
                            date.setMinutes(date.getMinutes() + 30);
                            line.occupied_at = date.toLocaleString("en-GB", {
                                year: "numeric",
                                month: "2-digit",
                                day: "2-digit",
                                hour: "2-digit",
                                minute: "2-digit",
                                second: "2-digit",
                                hour12: false
                            });
                        }
                        if (line.released_at) {
                            const date = new Date(line.released_at);
                            date.setHours(date.getHours() + 5);
                            date.setMinutes(date.getMinutes() + 30);
                            line.released_at = date.toLocaleString("en-GB", {
                                year: "numeric",
                                month: "2-digit",
                                day: "2-digit",
                                hour: "2-digit",
                                minute: "2-digit",
                                second: "2-digit",
                                hour12: false
                            });
                        }
                    });
                    deviceLineData.sort((a, b) => b.id - a.id);

                    // Attaching related device line data to each 'device.management' record
                    data.forEach(record => {
                        record.device_line_data = deviceLineData.filter(line => record.device_line_ids.includes(line.id));
                    });
                }
            }

            // Setting the fetched data to state
            this.state.devices = data || [];
            this.state.stats = this.processStats(data || []);

        } catch (error) {
            console.error("Error loading dashboard data:", error);
            this.state.stats = this.getEmptyStats();
        } finally {
            this.state.isLoading = false;
        }
    }

    getEmptyStats() {
        return {
            total: 0,
            available: 0,
            occupied: 0,
            byDepartment: {},
            byOS: {},
            byDeviceType: {},
            recentActivities: []
        };
    }

    openDeviceHistory(device) {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Devices History',
            res_model: 'device.line',
            views: [[false, 'list']],
            domain: [["device_id", "in", [device]]],
            target: 'new',
            search_view_id: [false],
            context: {
                group_by: ["occupied_at"],  // Group records by 'occupied_by'
                order: "occupied_at desc",
                create: false,  // Disable 'Create' button
            }
        });

        // this.action.doAction('device_management.action_device_line', {
        //     target: 'new',
        //     domain: [["device_id", "in", [device]]],
        // });

    }

    // openDeviceHistory1(device) {
    //     const self = this;
    //     this.orm.searchRead(
    //         'device.line',
    //         [['device_id', '=', device]],
    //         ['occupied_by', 'occupied_at', 'released_at']
    //     ).then(result => {
    //         const deviceHistory = [];

    //         // Grouping results by date
    //         let currentDate = '';
    //         result.forEach(record => {
    //             if (record.date !== currentDate) {
    //                 currentDate = record.date;
    //                 deviceHistory.push({
    //                     is_date: true,
    //                     date: currentDate
    //                 });
    //             }
    //             const occupiedTime = record.occupied_at.split(' ')[1];
    //             const releasedTime = record.released_at ? record.released_at.split(' ')[1] : 'Now';

    //             deviceHistory.push({
    //                 ...record,
    //                 occupied_time: occupiedTime,
    //                 released_time: releasedTime
    //             });
    //         });

    //         console.log("Debug----------- deviceHistory ---------->", deviceHistory);

    //         // Open Dialog
    //         this.env.services.dialog.add(Dialog, {
    //             title: "Device History",
    //             body: self.env.qweb.render('device_management.device_dashboard.OpenDeviceHistory', {
    //                 deviceHistory: deviceHistory,
    //             }),
    //             size: 'lg', // or 'md', 'xl'
    //         });
    //     });
    // }



    getDeviceTypes() {
        return Object.entries(this.state.stats.byDeviceType || {});
    }

    getDepartments() {
        return Object.entries(this.state.stats.byDepartment || {});
    }

    getRecentActivities() {
        return this.state.stats.recentActivities || [];
    }

    processStats(data) {
        const stats = this.getEmptyStats();
        stats.total = data.length;

        data.forEach(device => {
            // Count by status
            if (device.is_occupied) {
                stats.occupied++;
            } else {
                stats.available++;
            }

            // Count by department
            const deptName = device.department_id ? device.department_id[1] : 'Unassigned';
            stats.byDepartment[deptName] = (stats.byDepartment[deptName] || 0) + 1;

            // Count by OS version
            const os = device.os_version || 'Unknown';
            stats.byOS[os] = (stats.byOS[os] || 0) + 1;

            // Count by device type
            const type = device.device_type || 'Unknown';
            stats.byDeviceType[type] = (stats.byDeviceType[type] || 0) + 1;

            // Add to recent activities if occupied
            if (device.device_line_data && device.device_line_data[0]) {
                stats.recentActivities.push({
                    device: device.name || 'Unknown Device',
                    user: device.occupied_by ? device.occupied_by[1] : 'Unknown',
                    date: device.device_line_data[0].occupied_at ? device.device_line_data[0] : null,
                    type: device.is_occupied ? 'checked-out' : 'checked-in'
                });
            }
        });

        // Sort recent activities by date
        stats.recentActivities.sort((a, b) => new Date(b.date) - new Date(a.date));
        stats.recentActivities = stats.recentActivities.slice(0, 5);

        return stats;
    }

    openDeviceList(filters = {}) {
        const domain = Object.entries(filters).map(([key, value]) => [key, '=', value]);
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Devices',
            res_model: 'device.management',
            views: [[false, 'list'], [false, 'form']],
            domain: domain,
            target: 'current'
        });
    }

    filterDevices(filter) {
        this.state.filter = filter;
    }

    getFilteredDevices() {
        if (this.state.filter === 'all') {
            return this.state.devices;
        }
        if (this.state.filter === 'available') {
            return this.state.devices.filter(device => !device.is_occupied);
        }
        if (this.state.filter === 'occupied') {
            return this.state.devices.filter(device => device.is_occupied);
        }
        return [];
    }

    openDeviceForm(deviceId) {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'device.management',
            res_id: deviceId,
            views: [[false, 'form']],
            target: 'current',
            mode: 'readonly'
        });
    }
}

DeviceDashboard.template = 'device_management.Dashboard';

registry.category("actions").add("device_management.dashboard", DeviceDashboard); 