import json
import logging
import secrets
import werkzeug
import ast
from datetime import datetime, timedelta, date
from odoo import http, api, SUPERUSER_ID
from odoo.http import request
from odoo.exceptions import AccessDenied
from werkzeug.wrappers import Response

_logger = logging.getLogger(__name__)


# def _get_project_details(projectId, userId):
#     task = request.env["project.task"].sudo().search([('project_id', '=', int(projectId)), ('user_ids', '=', int(userId)), ('state', '!=', '1_done')])
#     project_list = request.env['project.project'].sudo().search([('id', '=', int(projectId))])
#     print("\n Debug --------------------- task _assign_project ----------------->", task, project_list)
#     list_task = [
#         {
#             "pdtid": "0",
#             "work_time_spent": 0,
#             "meet_time_spent": 0,
#             "pid": str(record_data.id),
#             "pname": record_data.name,
#             "active_time": 0,
#             "active_type": 0,
#             "unassigned": "true",
#             "hours": str(record_data.allocated_hours),
#             "tiIsAccountabilityReportVisible": 0,
#             "project_task": [
#                 {
#                     "iProjectTaskId": record.id,
#                     "vTask": record.name,
#                     "iTimeSpent": int(record.effective_hours * 3600),
#                     "tiIsActive": 1 if record.is_running_tt else 0,
#                     "vModule": "Manual",
#                     "iEstimatedTime": int(record.allocated_hours * 3600),
#                     "tiIsComplete": 0 if record.stage_id and record.stage_id.name.lower() == "done" else 1,
#                     "iProjectId": str(record.project_id.id),
#                     "iUserId": int(userId)
#                 } for record in task],
#         } for record_data in project_list
#     ]

#     print("\n Debug --------------------- list_task ----------------->", list_task)
#     return list_task


def _get_project_details(projectId, userId):
    try:
        project_id = int(projectId or 0)
        user_id = int(userId or 0)

        project = request.env['project.project'].sudo().browse(project_id)
        if not project.exists():
            _logger.warning("[Project Details] Project ID %s not found", project_id)
            return []

        tasks = request.env["project.task"].sudo().search([
            ('project_id', '=', project_id),
            ('user_ids', '=', user_id),
            ('state', '!=', '1_done')
        ])

        _logger.info("[Project Details] Fetched %d task(s) for user %s in project '%s'",
                     len(tasks), user_id, project.name)
        task_stage_object = request.env['project.task.type'].sudo().search([('project_ids', '=', project.id)])
        print("\n Debug --------------------- task_stage_object ----------------->", task_stage_object)
        task_stages = [stage.name for stage in task_stage_object]


        project_task_data = [
            {
                "iProjectTaskId": task.id,
                "vTask": f"({dict(task._fields['task_type'].selection).get(task.task_type)}) {task.name}",
                "iTimeSpent": int(task.effective_hours * 3600),
                "tiIsActive": 1 if task.is_running_tt else 0,
                "vMilestone": task.milestone_id.name if task.milestone_id else "Milestone",
                "vModule": "Manual" if not task.module_id else task.module_id.name,
                "iEstimatedTime": int(task.allocated_hours * 3600),
                "tiIsComplete": 0 if task.stage_id and task.stage_id.name.lower() == "done" else 1,
                "iProjectId": str(project.id),
                "vStatus": task_stages,
                "iUserId": user_id
            }
            for task in tasks
        ]

        result = [{
            "pdtid": "0",
            "work_time_spent": 0,
            "meet_time_spent": 0,
            "pid": str(project.id),
            "pname": project.name,
            "active_time": 0,
            "active_type": 0,
            "unassigned": "true",
            "hours": str(project.allocated_hours),
            "tiIsAccountabilityReportVisible": 0,
            "project_task": project_task_data,
        }]

        _logger.debug("[Project Details] Final result: %s", result)
        return result

    except Exception as e:
        _logger.exception("Error in _get_project_details: %s", str(e))
        return []



def get_authenticated_user():
    headers = request.httprequest.headers
    auth_header = headers.get("Authorization")
    if not auth_header or " " not in auth_header:
        return None
    api_key = auth_header.split(" ")[1]
    return (
        request.env["auth.api.key"]
        .sudo()
        .search([("key", "=", api_key)], limit=1)
        .user_id
    )


class ProjectList(http.Controller):

    @http.route("/user/get-project-managers", type="http", auth="api_key", methods=["GET"], csrf=False)
    def _get_manager_list(self, **kwargs):

        try:
            project_group = request.env.ref('custom_dashboard.group_dashboard_project_manager')
            ope_group = request.env.ref('custom_dashboard.group_dashboard_operation_manager')
            res_group = request.env.ref('custom_dashboard.group_dashboard_resource_manager')

            manager = request.env["res.users"].sudo().search([("groups_id", "in", [project_group.id, res_group.id, ope_group.id])])

            print("\n Debug --------------------- manager ----------------->", manager)

            manager_list = [
                {"id": record.id, "name": record.name} for record in manager
            ]

            return json.dumps({
                "responseCode": 200,
                "responseMessage": "success ",
                "responseData": manager_list,
            })
        except Exception as e:
            data = {
                "responseCode": 400,
                "responseMessage": "error",
                "responseData": []
            }
            _logger.error(e)
            return json.dumps(data)

    @http.route("/project/get-projects", type="http", auth="api_key", methods=["GET"], csrf=False)
    def _get_project_list(self, **kwargs):

        manager = kwargs.get("managerid")
        print(manager)
        try:
            if manager:
                project = request.env['project.project'].sudo().search([('user_id', '=', int(manager))])
                # print("\n Debug --------------------- project ----------------->", project)

            project_list = [
                {"id": str(record.id), "name": record.name} for record in project
            ]

            # print("\n Debug --------------------- project_list ----------------->", project_list)

            return json.dumps({
                "responseCode": 200,
                "responseMessage": "success ",
                "responseData": project_list,
            })
        except Exception as e:
            data = {
                "responseCode": 400,
                "responseMessage": "error",
                "responseData": []
            }
            _logger.error(e)
            return json.dumps(data)

    @http.route("/project/get-assigned-project", type="http", auth="api_key", methods=["POST"], csrf=False)
    def _get_assigned_projects(self, **kwargs):

        user = kwargs.get("userid")
        print(user)
        # Fetch projects assigned to the user
        try:
            if user:
                projects = request.env["project.project"].sudo().search([("user_id", "=", int(user))])
                print(projects)
                listProject = []
                for project in projects:
                    project_data = {
                        "pdtid": None,
                        "work_time_spent": 0,  # You may calculate this based on task times
                        "meet_time_spent": 0,  # If applicable, fetch meeting time spent
                        "pid": str(project.id),
                        "projectName": project.name,
                        "pname": project.name,
                        "active_time": "0",
                        "active_type": None,
                        "unassigned": "true",  # You can change this based on logic
                        "hours": str(project.allocated_hours * 3600 if project.allocated_hours else 0),  # Convert planned hours to seconds
                        "estimatedHours": str(project.allocated_hours * 3600 if project.allocated_hours else 0),
                        "workTypeActive": "false",
                        "meetTypeActive": "false",
                        "actual": 0,
                        "project_task": [],
                    }
                    # print("\n--------------------------- project_data --------------->", project_data)

                    # Fetch project tasks
                    tasks = request.env["project.task"].sudo().search([("project_id", "=", project.id)])
                    # print("\n--------------------------- tasks --------------->", tasks)
                    for task in tasks:
                        task_data = {
                            "iProjectTaskId": task.id,
                            "vTask": f"({dict(task._fields['task_type'].selection).get(task.task_type)}) {task.name}",
                            "iTimeSpent": int(task.effective_hours * 3600) if task.effective_hours else 0,  # Convert hours to seconds
                            "tiIsActive": 0,  # Modify if you have task active status logic
                            "vMilestone": task.milestone_id.name if task.milestone_id else "Milestone",
                            "vModule": "Manual" if not task.module_id else task.module_id.name,
                            "iEstimatedTime": int(task.allocated_hours * 3600) if task.allocated_hours else 0,  # Convert to seconds
                            "tiIsComplete": 1 if task.stage_id and task.stage_id.name.lower() == "done" else 0,
                            "iProjectId": str(task.project_id.id),
                            "iUserId": user,
                        }
                        project_data["project_task"].append(task_data)

                    listProject.append(project_data)
                    # print("Debug ----------------------- listProject -------------->", listProject)

                    data = {

                        "responseCode": 200,
                        "responseMessage": "success ",
                        "responseData": listProject,
                    }

                    return json.dumps(data)
        except Exception as e:
            data = {
                "responseCode": 400,
                "responseMessage": "error",
                "responseData": []
            }
            _logger.error(e)
            return json.dumps(data)

    @http.route("/project/get-project-task", type="http", auth="api_key", methods=["POST"], csrf=False)
    def _get_project_name(self, **kwargs):

        user = kwargs.get("userid")
        projectid = kwargs.get("projectid")

        try:

            tasks = request.env["project.task"].sudo().search([("project_id", "=", int(projectid)), ('user_ids', '=', int(user)), ('state', '!=', '1_done')])
            print("\n Debug --------------------- tasks _get_project_name ----------------->", tasks)
            task_list = [{
                "iProjectTaskId": record.id,
                "vTask": f"({dict(record._fields['task_type'].selection).get(record.task_type)}) {record.name}",
                "iTimeSpent": int(record.effective_hours * 3600),
                "tiIsActive": 1 if record.active else 0,
                "vMilestone": record.milestone_id.name if record.milestone_id else "Milestone",
                "vModule": "Manual" if not record.module_id else record.module_id.name,
                "iEstimatedTime": int(record.allocated_hours * 3600),
                "tiIsComplete": 0 if record.stage_id and record.stage_id.name.lower() == "done" else 1,
                "iProjectId": str(record.project_id.id),
                "iUserId": int(user)
            } for record in tasks]

            print("\n Debug --------------------- task_list _get_project_name ----------------->", task_list)

            return json.dumps({
                "responseCode": 200,
                "responseMessage": "success ",
                "responseData": task_list,
            })
        except Exception as e:
            data = {
                "responseCode": 400,
                "responseMessage": "error",
                "responseData": []
            }
            _logger.error(e)
            return json.dumps(data)

    # old code replace with new for dynamic update stage_id in project.task
    @http.route("/project/task-completed", type="http", auth="api_key", methods=["POST"], csrf=False)
    def _get_task_completed(self, **kwargs):
        taskId = kwargs.get("iProjectTaskId")
        user = get_authenticated_user()
        print("\n Debug --------------------- kwargs _get_task_completed ----------------->", kwargs, user)
        try:
            print("\n Debug --------------------- taskid _get_task_completed ----------------->", taskId)
            task = request.env["project.task"].sudo().search([('id', '=', int(taskId))])
            task.write({'state': "1_done"})
            project_list = task.project_id
            list_task = _get_project_details(project_list, user)

            data = {
                "responseCode": 200,
                "responseMessage": "Success",
                "responseData": list_task
            }
            return json.dumps(data)
        except Exception as e:
            data = {
                "responseCode": 400,
                "responseMessage": "error",
                "responseData": []
            }
            _logger.error(e)
            return json.dumps(data)

    
    # @http.route("/project/task-completed", type="http", auth="api_key", methods=["POST"], csrf=False)
    # def _get_task_completed(self, **kwargs):
    #     task_id = kwargs.get("iProjectTaskId")
    #     user = get_authenticated_user()
    #     _logger.info("=== [INFO] Incoming request to complete task ===")
    #     _logger.info(">>> User: %s | Input Data: %s", user.name, kwargs)
    #
    #     if not task_id:
    #         _logger.warning("!!! [WARN] Missing 'iProjectTaskId' in request payload !!!")
    #         return json.dumps({
    #             "responseCode": 400,
    #             "responseMessage": "Missing task ID",
    #             "responseData": []
    #         })
    #
    #     try:
    #         task = request.env["project.task"].sudo().browse(int(task_id))
    #         if not task.exists():
    #             _logger.warning("!!! [WARN] Task with ID %s not found in DB !!!", task_id)
    #             return json.dumps({
    #                 "responseCode": 404,
    #                 "responseMessage": "Task not found",
    #                 "responseData": []
    #             })
    #
    #         # Get current stage
    #         current_stage = task.stage_id
    #         project_stages = task.project_id.type_ids.sorted(key=lambda s: s.sequence)
    #
    #         next_stage = False
    #         for idx, stage in enumerate(project_stages):
    #             if stage.id == current_stage.id:
    #                 if idx + 1 < len(project_stages):
    #                     next_stage = project_stages[idx + 1]
    #                 break
    #
    #         if next_stage:
    #             task.write({'stage_id': next_stage.id})
    #             _logger.info(">>> [STAGE] Task %s moved from '%s' to next stage '%s'.",
    #                          task.id, current_stage.name, next_stage.name)
    #         else:
    #             _logger.info(">>> [STAGE] Task %s is already in the last stage '%s'. No move done.",
    #                          task.id, current_stage.name)
    #
    #         _logger.info(">>> [SUCCESS] Task ID %s marked as Done by %s", task.id, user.name)
    #
    #         project = task.project_id
    #         response_data = _get_project_details(project, user)
    #         _logger.debug("--- [DEBUG] Response data being returned: %s", response_data)
    #
    #         return json.dumps({
    #             "responseCode": 200,
    #             "responseMessage": "Success",
    #             "responseData": response_data
    #         })
    #
    #     except Exception as e:
    #         _logger.exception("!!! [ERROR] Exception occurred while completing task ID %s: %s", task_id, str(e))
    #         return json.dumps({
    #             "responseCode": 500,
    #             "responseMessage": "Internal server error",
    #             "responseData": []
    #         })

    @http.route("/project/assign-project", type="http", auth="api_key", methods=["POST"], csrf=False)
    def _assign_project(self, **kwargs):
        print("\n Debug --------------------- kwargs _assign_project ----------------->", kwargs)

        projectId = kwargs.get("projectId")
        managerId = kwargs.get("managerId")
        developerId = kwargs.get("developerId")
        work_type = kwargs.get("type")

        print("\n Debug --------------------- projectId _assign_project ----------------->", projectId, managerId, developerId, work_type)

        try:
            task = request.env["project.task"].sudo().search([('project_id', '=', int(projectId)), ('user_ids', '=', int(developerId))])
            project_list = request.env['project.project'].sudo().search([('id', '=', int(projectId))])
            print("\n Debug --------------------- task _assign_project ----------------->", task, project_list)

            list_task = _get_project_details(project_list, developerId)
            data = {
                "responseCode": 200,
                "responseMessage": "Success",
                "responseData": list_task
            }
            print("\n Debug --------------------- data _assign_project ----------------->", data)
            _logger.info("Task Timer Created Successfully.")
            return json.dumps(data)

        except Exception as e:
            data = {
                "responseCode": 400,
                "responseMessage": "error",
                "responseData": []
            }
            _logger.error(e)
            return json.dumps(data)

    # @http.route("/project/update-traker", type="http", auth="api_key", methods=["POST"], csrf=False)
    # def update_project_tracker(self, **kwargs):
    #     print("\n Debug --------------------- kwargs update_project_tracker ----------------->", kwargs)

    #     projectId = kwargs.get("projectId")
    #     taskId = kwargs.get("taskId")
    #     type = kwargs.get("type")

    #     request.env['ir.config_parameter'].sudo().set_param('time_tracker_odoo.update_traker', True)

    #     user_id = get_authenticated_user()
    #     print("DEBUG: user_id", user_id)

    #     def get_the_date_from_type(type):
    #         if type == "I":
    #             attendance_id.write({'interview_start_time': datetime.now(), 'last_activity_type': type})
    #         elif type == "B":
    #             attendance_id.write({'break_start_time': datetime.now(), 'last_activity_type': type})
    #         elif type == "L":
    #             attendance_id.write({'lunch_start_time': datetime.now(), 'last_activity_type': type})
    #         elif type == "G":
    #             attendance_id.write({'general_meeting_start_time': datetime.now(), 'last_activity_type': type})
    #         elif type == "F":
    #             attendance_id.write({'floor_start_time': datetime.now(), 'last_activity_type': type})
    #         elif type == "N":
    #             attendance_id.write({'no_work_start_time': datetime.now(), 'last_activity_type': type})
    #         elif type == "E":
    #             attendance_id.write({'estimate_start_time': datetime.now(), 'last_activity_type': type})
    #         elif type == "R":
    #             attendance_id.write({'r_and_d_start_time': datetime.now(), 'last_activity_type': type})

    #     try:
    #         with request.env.cr.savepoint():
    #             env = request.env
    #             hr_attendance = env["hr.attendance"].sudo()
    #             project_task = env["project.task"].sudo()
    #             project_project = env["project.project"].sudo()
    #             analytic_line = env["account.analytic.line"].sudo()

    #             today = datetime.now().date()

    #             attendance_id = hr_attendance.search([
    #                 ('employee_id', '=', user_id.employee_id.id),
    #                 ("check_in", ">=", today.strftime("%Y-%m-%d 00:00:00")),
    #                 ("check_in", "<=", today.strftime("%Y-%m-%d 23:59:59")),
    #             ])

    #             end_time_fields = {
    #                 'I': 'interview_end_time',
    #                 'B': 'break_end_time',
    #                 'L': 'lunch_end_time',
    #                 'G': 'general_meeting_end_time',
    #                 'F': 'floor_end_time',
    #                 'N': 'no_work_end_time',
    #                 'E': 'estimate_end_time',
    #                 'R': 'r_and_d_end_time',
    #             }

    #             if attendance_id.last_activity_type in ['I', 'B', 'L', 'G', 'F', 'N', 'E', 'R'] and type in ['W', 'M']:
    #                 last_activity_type = attendance_id.last_activity_type
    #                 print("\n Debug --------------------- last_activity_type update_project_tracker while in if and type in ['W', 'M'] ----------------->", last_activity_type)
    #                 if last_activity_type in end_time_fields:
    #                     attendance_id.write({end_time_fields[last_activity_type]: datetime.now()})
    #                 attendance_id.write({'last_activity_type': False})

    #             if type not in ['W', 'M']:
    #                 last_task = project_task.search([('user_ids', '=', user_id.id), ('is_running_tt', '=', True)], limit=1)
    #                 print("\n Debug --------------------- last_task update_project_tracker while in if and type not in ['W', 'M'] ----------------->", last_task)
    #                 print("\n Debug --------------------- last_task update_project_tracker while in if and type not in ['W', 'M'] ----------------->", last_task.task_update_from_tt, last_task.name)
    #                 if last_task and last_task.task_update_from_tt:
    #                     last_task.sudo().write({"task_update_from_tt": False, 'is_running_tt': False})
    #                     last_ts = analytic_line.search([
    #                         ('date', '=', date.today()), ('employee_id', '=', user_id.employee_id.id), ('task_id', '=', last_task.id)
    #                     ], limit=1)
    #                     print("\n Debug --------------------- last_ts update_project_tracker while in if and type not in ['W', 'M'] ----------------->", last_ts, last_ts.name)
    #                     if last_ts:
    #                         data_update = last_ts.sudo().write({'end_time': datetime.now()})
    #                         print("\n Debug --------------------- data_update update_project_tracker while in if and type not in ['W', 'M'] ----------------->", data_update)

    #             if taskId != 'null' or projectId != 'null' and type in ['W', 'M']:
    #                 task = project_task.search([('id', '=', int(taskId))]) if taskId != 'null' else None
    #                 last_task = project_task.search([('user_ids', '=', user_id.id), ('is_running_tt', '=', True)], limit=1)
    #                 project_list = project_project.search([('id', '=', int(projectId))]) if projectId != 'null' else None

    #                 meeting_task = project_task.search([('type', '=', 'M'), ('project_id', '=', int(projectId))],
    #                                                    order="create_date desc", limit=1) if projectId else None
    #                 today = date.today()

    #                 # if taskId != 'null':
    #                 #     timesheet_id = analytic_line.search([
    #                 #         ('task_id', '=', int(taskId)), ('date', '=', today)
    #                 #     ], limit=1)
    #                 # else:
    #                 #     timesheet_id = analytic_line.search([
    #                 #         ('task_id', '=', meeting_task.id), ('date', '=', today)
    #                 #     ])

    #                 print("\n Debug --------------------- last_task update_project_tracker while in if----------------->", last_task, task, meeting_task)

    #                 if last_task:
    #                     if last_task.task_update_from_tt:
    #                         last_ts = analytic_line.search([
    #                             ('date', '=', today), ('employee_id', '=', user_id.employee_id.id), ("task_id", "=", last_task.id)
    #                         ], order="write_date desc", limit=1)

    #                         print("\n Debug --------------------- last_ts update_project_tracker while in if----------------->", last_ts)

    #                         if last_ts:
    #                             last_ts.write({'end_time': datetime.now()})

    #                     last_task.write({"task_update_from_tt": False, 'is_running_tt': False})

    #                 if task:
    #                     task.write({"task_update_from_tt": type, 'is_running_tt': True})
    #                 else:
    #                     meeting_task.write({"task_update_from_tt": type, 'is_running_tt': True})

    #                 if type == "W":
    #                     timesheet_id = analytic_line.create({
    #                         'name': task.name,
    #                         'project_id': task.project_id.id,
    #                         'task_id': task.id,
    #                         'user_id': user_id.id,
    #                         'date': datetime.now(),
    #                         'start_time': datetime.now(),
    #                     })


    #                 # elif timesheet_id and type == "W":
    #                 #     timesheet_id.write({'start_time': datetime.now()})


    #                 elif type == "M" and meeting_task:
    #                     timesheet_id = analytic_line.create({
    #                         'name': f"{meeting_task.name} Meeting",
    #                         'project_id': meeting_task.project_id.id,
    #                         'task_id': meeting_task.id,
    #                         'user_id': user_id.id,
    #                         'date': datetime.now(),
    #                         'start_time': datetime.now(),
    #                     })

    #                 # print("\n Debug --------------------- timesheet_id update_project_tracker while in if----------------->", timesheet_id)
    #                 # elif timesheet_id and type == "M":
    #                 #     timesheet_id.write({'start_time': datetime.now()})

    #                 print("\n Debug --------------------- last_task.task_update_from_tt ----------------->",
    #                       last_task)
    #                 print("\n Debug --------------------- last_task.task_update_from_tt ----------------->",
    #                       last_task.task_update_from_tt)

    #             if taskId == 'null' or projectId == 'null' and type not in ['W', 'M']:
    #                 print("\n Debug --------------------- attendance_id update_project_tracker else----------------->", attendance_id)

    #                 if attendance_id:
    #                     last_activity_type = attendance_id.last_activity_type

    #                     if last_activity_type in end_time_fields:
    #                         attendance_id.write({end_time_fields[last_activity_type]: datetime.now()})

    #                     get_the_date_from_type(type)

    #             _logger.info("Time Updated for User: %s", user_id.id)
    #             return json.dumps({"responseCode": 200, "responseMessage": "Success", "responseData": []})

    #     except Exception as e:
    #         _logger.error("Error: %s", e)
    #         return json.dumps({"responseCode": 400, "responseMessage": "error", "responseData": []})

    
    import json
    import logging
    from datetime import datetime, date
    from odoo import http
    from odoo.http import request

    _logger = logging.getLogger(__name__)


    class ProjectTrackerController(http.Controller):

        @http.route("/project/update-traker", type="http", auth="api_key", methods=["POST"], csrf=False)
        def update_project_tracker(self, **kwargs):
            _logger.info("=== [TRACKER] Incoming update request: %s", kwargs)

            projectId = kwargs.get("projectId")
            taskId = kwargs.get("taskId")
            type = kwargs.get("type")

            request.env['ir.config_parameter'].sudo().set_param('time_tracker_odoo.update_traker', True)
            user_id = get_authenticated_user()
            _logger.info(">>> [USER] Authenticated User: %s (Employee ID: %s)", user_id.name, user_id.employee_id.id)

            def get_the_date_from_type(_type):
                time_field_map = {
                    "I": 'interview_start_time',
                    "B": 'break_start_time',
                    "L": 'lunch_start_time',
                    "G": 'general_meeting_start_time',
                    "F": 'floor_start_time',
                    "N": 'no_work_start_time',
                    "E": 'estimate_start_time',
                    "R": 'r_and_d_start_time'
                }
                if _type in time_field_map:
                    attendance_id.write({
                        time_field_map[_type]: datetime.now(),
                        'last_activity_type': _type
                    })
                    _logger.info(">>> [ATTENDANCE] Start time set for activity type '%s'", _type)

            try:
                with request.env.cr.savepoint():
                    env = request.env
                    hr_attendance = env["hr.attendance"].sudo()
                    project_task = env["project.task"].sudo()
                    project_project = env["project.project"].sudo()
                    analytic_line = env["account.analytic.line"].sudo()
                    today = datetime.now().date()

                    attendance_id = hr_attendance.search([
                        ('employee_id', '=', user_id.employee_id.id),
                        ("check_in", ">=", today.strftime("%Y-%m-%d 00:00:00")),
                        ("check_in", "<=", today.strftime("%Y-%m-%d 23:59:59")),
                    ])

                    end_time_fields = {
                        'I': 'interview_end_time', 'B': 'break_end_time',
                        'L': 'lunch_end_time', 'G': 'general_meeting_end_time',
                        'F': 'floor_end_time', 'N': 'no_work_end_time',
                        'E': 'estimate_end_time', 'R': 'r_and_d_end_time',
                    }

                    # Closing last activity before starting W/M
                    if attendance_id.last_activity_type in end_time_fields and type in ['W', 'M']:
                        end_field = end_time_fields[attendance_id.last_activity_type]
                        attendance_id.write({
                            end_field: datetime.now(),
                            'last_activity_type': False
                        })
                        _logger.info(">>> [ATTENDANCE] Closed last activity: %s", attendance_id.last_activity_type)

                    # Stop previous task tracking
                    if type not in ['W', 'M']:
                        last_task = project_task.search([
                            ('user_ids', '=', user_id.id),
                            ('is_running_tt', '=', True)
                        ], limit=1)

                        if last_task and last_task.task_update_from_tt:
                            _logger.info(">>> [TASK] Ending previous running task: %s", last_task.name)
                            last_task.write({"task_update_from_tt": False, 'is_running_tt': False})

                            last_ts = analytic_line.search([
                                ('date', '=', today),
                                ('employee_id', '=', user_id.employee_id.id),
                                ('task_id', '=', last_task.id)
                            ], limit=1)
                            if last_ts:
                                last_ts.write({'end_time': datetime.now()})
                                _logger.info(">>> [TIMESHEET] Closed timesheet for task: %s", last_task.name)

                    # Start working on task or meeting
                    if (taskId != 'null' or projectId != 'null') and type in ['W', 'M']:
                        task = project_task.search([('id', '=', int(taskId))]) if taskId != 'null' else None
                        meeting_task = project_task.search([
                            ('type', '=', 'M'),
                            ('project_id', '=', int(projectId))
                        ], order="create_date desc", limit=1) if projectId != 'null' else None

                        last_task = project_task.search([
                            ('user_ids', '=', user_id.id),
                            ('is_running_tt', '=', True)
                        ], limit=1)

                        if last_task:
                            if last_task.task_update_from_tt:
                                last_ts = analytic_line.search([
                                    ('date', '=', today),
                                    ('employee_id', '=', user_id.employee_id.id),
                                    ("task_id", "=", last_task.id)
                                ], order="write_date desc", limit=1)

                                if last_ts:
                                    last_ts.write({'end_time': datetime.now()})
                                    _logger.info(">>> [TIMESHEET] Closed last task timesheet: %s", last_task.name)

                            last_task.write({"task_update_from_tt": False, 'is_running_tt': False})

                        # Auto move stage 1 → 2
                        if task:
                            task.write({"task_update_from_tt": type, 'is_running_tt': True})
                            # Move only if current stage is sequence 1 → to project-specific stage with sequence 2
                            if task.stage_id and task.stage_id.sequence == 1:
                                stage_2 = task.project_id.type_ids.filtered(lambda s: s.sequence == 2)
                                if stage_2:
                                    old_stage_name = task.stage_id.name
                                    task.write({'stage_id': stage_2.id})
                                    _logger.info(">>> [STAGE-MOVE] Task '%s' moved from '%s' ➜ '%s' (project stage 1 ➜ 2)",
                                                             task.name, old_stage_name, stage_2.name)
                                else:
                                    _logger.warning("!!! [STAGE-MOVE] No stage with sequence=2 found in project '%s' for task '%s'",
                                                                task.project_id.name, task.name)
                            else:
                                _logger.info(">>> [STAGE-MOVE] Task '%s' is already in stage 2", task.name)
                        else:
                            meeting_task.write({"task_update_from_tt": type, 'is_running_tt': True})

                        if type == "W" and task:
                            analytic_line.create({
                                'name': task.name,
                                'project_id': task.project_id.id,
                                'task_id': task.id,
                                'user_id': user_id.id,
                                'date': datetime.now(),
                                'start_time': datetime.now(),
                            })
                            _logger.info(">>> [TIMESHEET] Started working on task: %s", task.name)

                        elif type == "M" and meeting_task:
                            analytic_line.create({
                                'name': f"{meeting_task.name} Meeting",
                                'project_id': meeting_task.project_id.id,
                                'task_id': meeting_task.id,
                                'user_id': user_id.id,
                                'date': datetime.now(),
                                'start_time': datetime.now(),
                            })
                            _logger.info(">>> [TIMESHEET] Started meeting task: %s", meeting_task.name)

                    # Handle general activity types (E.g., B, L, N...)
                    if (taskId == 'null' or projectId == 'null') and type not in ['W', 'M']:
                        if attendance_id:
                            last_activity_type = attendance_id.last_activity_type
                            if last_activity_type in end_time_fields:
                                attendance_id.write({end_time_fields[last_activity_type]: datetime.now()})
                            get_the_date_from_type(type)

                    _logger.info("✅ [TRACKER] Time Updated for User ID: %s", user_id.id)
                    return json.dumps({"responseCode": 200, "responseMessage": "Success", "responseData": []})

            except Exception as e:
                _logger.exception("❌ [TRACKER ERROR] Failed to update time tracker: %s", str(e))
                return json.dumps({"responseCode": 400, "responseMessage": "error", "responseData": []})

    @http.route("/project/add-project-task", type="http", auth="api_key", methods=["POST"], csrf=False)
    def _add_project_task(self, **kwargs):
        try:
            print("\n Debug --------------------- kwargs _add_project_task ----------------->", kwargs)

            projectId = kwargs.get("projectId")
            taskName = kwargs.get("taskName")
            userId = kwargs.get("userId")
            estimatedTime = kwargs.get("estimatedTime")

            if not projectId or not taskName or not userId:
                return json.dumps({
                    "responseCode": 400,
                    "responseMessage": "Missing required parameters: projectId, taskName, or userId"
                })

            projectId = int(projectId)
            userId = int(userId)
            allocated_hours = float(estimatedTime) / 3600 if estimatedTime else 0.0

            print("\n Debug --------------------- projectId ----------------->", projectId, userId, taskName,
                  estimatedTime)

            task = request.env["project.task"].sudo().create({
                "name": taskName,
                "project_id": projectId,
                "user_ids": [(6, 0, [userId])],
                "allocated_hours": allocated_hours
            })

            print("\n Debug --------------------- new task ----------------->", task)

            project_list = request.env['project.task'].sudo().search([('project_id', '=', projectId)])

            list_task = _get_project_details(project_list, userId)
            print("\n Debug --------------------- list_task _add_project_task ----------------->", list_task)
            _logger.info("New task created: %s", task)
            return json.dumps({
                "responseCode": 200,
                "responseMessage": "success",
                "responseData": list_task,
            })

        except ValueError as ve:
            _logger.error("Error while creating new task: %s", ve)
            return json.dumps({
                "responseCode": 400,
                "responseMessage": f"Invalid input: {str(ve)}"
            })
        except Exception as e:
            _logger.error("Error while creating new task: %s", e)
            return json.dumps({
                "responseCode": 500,
                "responseMessage": f"An error occurred: {str(e)}"
            })

    @http.route("/project/add-meeting-users", type="http", auth="api_key", methods=["POST"], csrf=False)
    def _add_project_meeting(self, **kwargs):
        user_list = []
        print("\n Debug --------------------- kwargs _add_project_meeting ----------------->", kwargs)
        user_ids = ast.literal_eval(kwargs.get("userIdsLeftSquareBracketRightSquareBracket"))

        projectId = kwargs.get("projectId")

        login_user = get_authenticated_user()
        print("\n Debug --------------------- login_user _add_project_meeting ----------------->", login_user)

        user_list.append(login_user.id)
        user_list = user_list + user_ids
        print("\n Debug --------------------- user_list _add_project_meeting ----------------->", user_list)
        try:
            if user_ids:
                with request.env.cr.savepoint():
                    task_id = request.env["project.task"].sudo().create({
                        'name': f"Meeting - {(datetime.now() + timedelta(hours=5, minutes=30)).strftime('%Y-%m-%d %H:%M:%S')}",
                        'user_ids': [(6, 0, user_list)],
                        'project_id': int(projectId),
                        'is_meeting_task': True,
                        # 'type': 'M'
                    })
                # request.env.cr.flush()
                # request.env.cr.commit()
                print("\n Debug --------------------- task_id _add_project_meeting ----------------->", task_id)

                return json.dumps({
                    "responseCode": 200,
                    "responseMessage": "success",
                    "responseData": user_ids
                })

        except Exception as e:
            _logger.error("Error while creating new meeting: %s", e)
            return json.dumps({
                "responseCode": 400,
                "responseMessage": f"An error occurred: {str(e)}"
            })
