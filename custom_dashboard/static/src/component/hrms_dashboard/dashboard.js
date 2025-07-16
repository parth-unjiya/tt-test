/** @odoo-module **/

import { Component, useState, onWillStart, useRef, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { DateTimeInput } from "@web/core/datetime/datetime_input";
import { loadBundle } from "@web/core/assets";

const { DateTime } = luxon;


export class Dashboard extends Component {
	static props = ["*"];
    // groups wise
    // Timesheet (employee)
    // Employee (Hr)
    // Project (TeamLead)
    // Admin
    // Hr dashboard bday list
    // Employee details of leaves

    setup() {
        this.user = useService("user");
        this.orm = useService("orm");
        this.action = useService("action");
        this.root = useRef("root");
        
		this.state = useState({
            login_employee: null,
            employee_counts: null,
            project_summary: null,
            task_summary: null,
            project_stage:null,
            tasks_stage: null,
            leave_request: null,
            manager_leave_request: null,
            attendance_data: null,
            birthday_list: null,
            showEmployeeData: false,
            showHrData: false,
            showAdminData: false,
            showResourceManagerData: false,
            showProjectData: false,
            showOperationManagerData: false,
            interview_data:null,
            department_data: null,
            employee_data: null,
            timesheetDateRange: null,
            employeeData: null,
            selectedMonth: "",
            selectedMonthPTS: "",
            PtsUser: false,
            PtsFilter: false,
            project_milestone: null,
            top_projects: null,
            absentees_list: null,
            department_id: null,
            start_date: null,
            end_date: null,
            employeeTotalActivityTime: null,
		});

        // hasGroup
        onWillStart(async () => {

            await loadBundle({
                cssLibs: [
                    "https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css",
                    "https://cdn.jsdelivr.net/npm/flatpickr/dist/plugins/monthSelect/style.css",
                ],

                jsLibs: [
                    "https://cdn.jsdelivr.net/npm/flatpickr",
                    "https://cdn.jsdelivr.net/npm/flatpickr/dist/plugins/monthSelect/index.js"
                ],
            });


            try {
                // Employee Details
                const empDetails = await this.orm.call('hr.employee', 'get_user_employee_details', [])
                console.log("============>", empDetails)
                if ( empDetails ){
                    this.state.login_employee = empDetails[0]
                }
                // Employee Counts
                const empCounts = await this.orm.call('hr.employee', 'get_employee_other_details', ['this_month'])
                if ( empCounts ){
                    this.state.employee_counts = empCounts
                }
                console.log("empCounts Details: ", empCounts);

                // Project Details
                const projectSummary = await this.orm.call('hr.employee', 'get_user_projects_summary', ['all'])
                if (projectSummary){
                    this.state.project_summary = projectSummary
                }
                
                // Task Details
                const taskSummary = await this.orm.call('hr.employee', 'get_user_task_summary', ['this_month', false])
                if (taskSummary){
                    this.state.task_summary = taskSummary
                }
                
                // Project Stage
                const projectStage = await this.orm.call('hr.employee', 'get_project_stage', [])
                if (projectStage){
                    this.state.project_stage = projectStage
                }
                
                // Employee Leaves
                const leaveRequest = await this.orm.call('hr.employee', 'get_employee_leave_request', ['this_week', false])
                if (leaveRequest){
                    this.state.leave_request = leaveRequest
                }

                // Show Manager Leaves Request
                const managerRequest = await this.orm.call('hr.employee', 'get_manager_leave_request', ['this_week', false])
                if (managerRequest){
                    this.state.manager_leave_request = managerRequest
                }
                
                // Attendance
                const attendanceData = await this.orm.call('hr.employee', 'get_attendance_data', ['this_week', false])
                if (attendanceData){
                    this.state.attendance_data = attendanceData
                }

                // Birthday List
                const birthdayList = await this.orm.call('hr.employee', 'get_birthdays_today', [])
                if (birthdayList){
                    this.state.birthday_list = birthdayList
                }

                // interview_data
                const interviewData = await this.orm.call('hr.employee', 'get_candidate_interview_data', [])
                if (interviewData){
                    this.state.interview_data = interviewData
                }

                // get departments
                const departmentData = await this.orm.call('hr.employee', 'get_department', [])
                if (departmentData){
                    this.state.department_data = departmentData
                }

                // get employee data
                const employeeRecords = await this.orm.call('hr.employee', 'get_employee_data', [])
                if (employeeRecords){
                    this.state.employee_data = employeeRecords
                }

                // get project milestone
                const projectMilestone = await this.orm.call('hr.employee', 'get_project_milestone', [])
                if (projectMilestone){
                    this.state.project_milestone = projectMilestone
                }

                // get Top 10 Project Highly Consume Hours
                const topProjects = await this.orm.call('hr.employee', 'get_top_projects_by_timesheet', [])
                if (topProjects){
                    this.state.top_projects = topProjects   
                }

                // get absentees list
                const absenteesList = await this.orm.call('hr.employee', 'get_absentees_details', [])
                if (absenteesList){
                    this.state.absentees_list = absenteesList   
                }

                // Check User Group
                const hrGroup = await this.user.hasGroup('custom_dashboard.group_dashboard_hr');
                const adminGroup = await this.user.hasGroup('custom_dashboard.group_dashboard_admin');
                const resourceManagerGroup = await this.user.hasGroup('custom_dashboard.group_dashboard_resource_manager');
                const projectManagerGroup = await this.user.hasGroup('custom_dashboard.group_dashboard_project_manager');
                const operationManagerGroup = await this.user.hasGroup('custom_dashboard.group_dashboard_operation_manager');
                const EmployeeGroup = await this.user.hasGroup('custom_dashboard.group_dashboard_employee');

                // Set visibility based on group membership
                if (hrGroup) {
                    this.state.showHrData = true;
                }

                if (adminGroup) {
                    this.state.showAdminData = true;
                }

                if (resourceManagerGroup) {
                    this.state.showResourceManagerData = true;
                }

                if (projectManagerGroup) {
                    this.state.showProjectData = true;
                }

                if (operationManagerGroup) {
                    this.state.showOperationManagerData = true;
                }

                if (EmployeeGroup) {
                    this.state.showEmployeeData = true;
                }
                
            } catch (error) {
                console.error("Error loading dashboard data:", error);
            }
            
            
        });

        onMounted(async () => {
			console.log(".........onMounted");
		});
	}

    // ============================= Onchange Actions here =============================

    async onChangeProjectStage(stage) {
        try {
            console.log("=============== Stage changed: ", stage);
            const projectSummary = await this.orm.call('hr.employee', 'get_user_projects_summary', [stage]);
            if (projectSummary) {
                this.state.project_summary = projectSummary;
            }
        } catch (error) {
            console.error("Error updating project stage:", error);
        }
    }

    async onChangeTask(filter_type) {
        var newFilter = filter_type;
        if (['this_day', 'this_month', 'this_week'].includes(filter_type)) {
            newFilter = filter_type;
            console.log("=============== In If Values ======== : ", newFilter, this.state.selectedMonth);
        }
        else {
            this.state.selectedMonth = filter_type;
            newFilter = 'custom_month';
            console.log("=============== In Else Values ======== : ", newFilter, this.state.selectedMonth);
        }
        try {
            const taskSummary = await this.orm.call('hr.employee', 'get_user_task_summary', [newFilter, this.state.selectedMonth]);
            if (taskSummary) {
                this.state.task_summary = taskSummary;
            }
        } catch (error) {
            console.error("Error updating task summary:", error);
        }
    }

    async onChangeAttendances(filter_type) {
        console.log("=============== Initial Values ========= ", this.state.selectedMonth, filter_type);
        var newFilter = filter_type;
        if (['this_day', 'this_month', 'this_week'].includes(filter_type)) {
            newFilter = filter_type;
            console.log("=============== In If Values ======== : ", newFilter, this.state.selectedMonth);
        }
        else {
            this.state.selectedMonth = filter_type;
            newFilter = 'custom_month';
            console.log("=============== In Else Values ======== : ", newFilter, this.state.selectedMonth);
        }
        try {
            console.log("=============== Data ======== : ", newFilter, this.state.selectedMonth);
            const attendanceData = await this.orm.call('hr.employee', 'get_attendance_data', [newFilter, this.state.selectedMonth]);
            if (attendanceData) {
                this.state.attendance_data = attendanceData;
            }
        } catch (error) {
            console.error("Error updating attendance data:", error);
        }
    }

    async onChangeCounts(filter_type) {
        try {
            const empCounts = await this.orm.call('hr.employee', 'get_employee_other_details', [filter_type])
            if ( empCounts ){
                this.state.employee_counts = empCounts
            }
        } catch (error) {
            console.error("Error updating employee_counts data:", error);
        }    
    }

    async onChangeLeaveRequest(filter_type) {
        var newFilter = filter_type;
        if (['this_day', 'this_month', 'this_week'].includes(filter_type)) {
            newFilter = filter_type;
            console.log("=============== In If Values ======== : ", newFilter, this.state.selectedMonth);
        }
        else {
            this.state.selectedMonth = filter_type;
            newFilter = 'custom_month';
            console.log("=============== In Else Values ======== : ", newFilter, this.state.selectedMonth);
        }
        try {
            const leaveRequest = await this.orm.call('hr.employee', 'get_employee_leave_request', [newFilter, this.state.selectedMonth])
            if (leaveRequest){
                this.state.leave_request = leaveRequest
            }
        } catch (error) {
            console.error("Error updating Leave Request data:", error);
        }    
    }

    async onChangeManagerLeaveRequest(filter_type) {
        var newFilter = filter_type;
        if (['this_day', 'this_month', 'this_week'].includes(filter_type)) {
            newFilter = filter_type;
            console.log("=============== In If Values ======== : ", newFilter, this.state.selectedMonth);
        }
        else {
            this.state.selectedMonth = filter_type;
            newFilter = 'custom_month';
            console.log("=============== In Else Values ======== : ", newFilter, this.state.selectedMonth);
        }
        try {
            const managerRequest = await this.orm.call('hr.employee', 'get_manager_leave_request', [newFilter, this.state.selectedMonth])
            if (managerRequest){
                this.state.manager_leave_request = managerRequest
            }
        } catch (error) {
            console.error("Error updating Manager Request data:", error);
        }    
    }

    async onDepartmentChange(department_id) {
        try {
            console.log("===============department_id: ", department_id);
            this.state.department_id = department_id
            const employeeRecords = await this.orm.call('hr.employee', 'get_employee_data', [department_id])
            if (employeeRecords){
                this.state.employee_data = employeeRecords
            }
        } catch (error) {
            console.error("Error updating Manager Request data:", error);
        }    
    }

    async onChangeDateRange(filter_type) {
        console.log("=============== Initial Values ========= ", this.state.employeeData, filter_type);
        this.state.PtsFilter = filter_type;
        if (['this_day', 'this_month', 'this_week'].includes(filter_type)) {
            this.state.PtsFilter = filter_type;
            console.log("=============== In If Values ======== : ", this.state.PtsFilter, this.state.selectedMonthPTS);
        }
        else {
            this.state.selectedMonthPTS = filter_type;
            this.state.PtsFilter = 'custom_month';
            console.log("=============== In Else Values ======== : ", this.state.PtsFilter, this.state.selectedMonthPTS);
        }
        try {
            const timesheetData = await this.orm.call('hr.employee', 'get_employee_timesheet', [this.state.PtsFilter, this.state.PtsUser, this.state.selectedMonthPTS])
            if (timesheetData){
                this.state.employeeData = timesheetData
            }
            console.log("=============EmployeeData============== : ", this.state.employeeData);
        } catch (error) {
            console.error("Error updating Leave Request data:", error);
        }
    }

    async onEmployeeChange(filter_type) {
        console.log("=============== Initial Values ========= ", this.state.PtsFilter, filter_type, this.state.selectedMonthPTS);
        this.state.PtsUser = filter_type;
        if (this.state.PtsFilter == false) {
            this.state.PtsFilter = 'this_week';
        }
        console.log("=====onEmployeeChange============== added data ======== : ", this.state.PtsFilter, this.state.PtsUser, this.state.selectedMonthPTS);
        try {
            const employeeRequest = await this.orm.call('hr.employee', 'get_employee_timesheet', [this.state.PtsFilter, this.state.PtsUser, this.state.selectedMonthPTS])
            if (employeeRequest){
                this.state.employeeData = employeeRequest
            }
            console.log("=============EmployeeData============== : ", this.state.employeeData);
        } catch (error) {
            console.error("Error updating Leave Request data:", error);
        }
    }

    async onClickResourceTimeSpent(ev){

        const startDateStr = document.querySelector("#start_date")?.value?.trim();
        const endDateStr = document.querySelector("#end_date")?.value?.trim();
        const department_id = this.state.department_id;
        const employee_id = this.state.PtsUser;

        // Check if any field is empty
        if (!startDateStr || !endDateStr || !department_id || !employee_id) {
            alert("Please select all required fields: Start Date, End Date, Department, and Employee.");
            // this.env.services.notification.add({
            //     title: "Missing Data",
            //     message: "Please select all required fields: Start Date, End Date, Department, and Employee.",
            //     type: "warning",
            // });
            // return;
        }

        // Parse date using Luxon
        const startDate = DateTime.fromFormat(startDateStr, "dd-MM-yyyy");
        const endDate = DateTime.fromFormat(endDateStr, "dd-MM-yyyy");

        // Format for Odoo: "YYYY-MM-DD"
        const startFormatted = startDate.toFormat("yyyy-MM-dd");
        const endFormatted = endDate.toFormat("yyyy-MM-dd");

        if (!startDate.isValid || !endDate.isValid) {
            alert("Invalid date format. Please select valid Start and End dates.");
            return;
        }

        if (startDate.toMillis() > endDate.toMillis()) {
            alert("Start Date cannot be after End Date.");
            return;
        }

        const employeeTotalActivityTime = await this.orm.call('hr.employee', 'get_employee_total_activity_time', [employee_id, startFormatted, endFormatted])
        console.log("=============employeeTotalActivityTime============== : ", employeeTotalActivityTime);
        this.state.employeeTotalActivityTime = employeeTotalActivityTime
    }

    // ============================= Redirect Actions here =============================
    hr_payslip() {
        this.action.doAction({
            name: _t("Employee Payslips"),
            type: 'ir.actions.act_window',
            res_model: 'hr.payslip',
            view_mode: 'tree,form,calendar',
            views: [[false, 'list'],[false, 'form']],
            domain: [['employee_id','=', parseInt(this.state.login_employee['id'])]],
            target: 'current'
        });
    }

    hr_timesheets() {
        this.action.doAction({
            name: _t("Timesheets"),
            type: 'ir.actions.act_window',
            res_model: 'account.analytic.line',
            view_mode: 'tree,form',
            views: [[false, 'list'], [false, 'form']],
            context: {
                'search_default_groupby_month': true,
            },
            domain: [['employee_id','=', parseInt(this.state.login_employee['id'])]],
            target: 'current'
        })
    }

    hr_leave() {
        this.action.doAction({
            name: _t("Employee Payslips"),
            type: 'ir.actions.act_window',
            res_model: 'hr.leave',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['employee_id','=', parseInt(this.state.login_employee['id'])]],
            target: 'current'
        });
    }

    job_applications(){
        this.action.doAction({
            name: _t("Applications"),
            type: 'ir.actions.act_window',
            res_model: 'hr.applicant',
            view_mode: 'tree,kanban,form,pivot,graph,calendar',
            views: [[false, 'list'],[false, 'kanban'],[false, 'form'],
                    [false, 'pivot'],[false, 'graph'],[false, 'calendar']],
            context: {},
            domain: [['user_id','=', parseInt(this.state.login_employee['user_id'][0])]],
            target: 'current'
        })
    }

}

Dashboard.template = "custom_dashboard.dashboard";
Dashboard.components = { DateTimeInput };
registry.category("actions").add("custom_dashboard", Dashboard);