import json
import logging
import secrets
import werkzeug
import base64
import io

from PIL import Image, UnidentifiedImageError
from datetime import datetime, timedelta, timezone
from collections import defaultdict

from odoo import http, api, SUPERUSER_ID
from odoo.http import request
from odoo.exceptions import AccessDenied
from werkzeug.wrappers import Response

from odoo import fields


_logger = logging.getLogger(__name__)


def configured_buttons():

    configured_buttons = [
        {
            "iConfiguredButtonId": 1,
            "vButtonName": "Lunch",
            "cButtonType": "L",
            "vButtonId": "lunchTime",
        },
        {
            "iConfiguredButtonId": 2,
            "vButtonName": "Break",
            "cButtonType": "B",
            "vButtonId": "breakTime",
        },
        {
            "iConfiguredButtonId": 3,
            "vButtonName": "Estimation",
            "cButtonType": "E",
            "vButtonId": "estimationTime",
        },
        {
            "iConfiguredButtonId": 4,
            "vButtonName": "Interview",
            "cButtonType": "I",
            "vButtonId": "interviewTime",
        },
        {
            "iConfiguredButtonId": 5,
            "vButtonName": "Floor Activity",
            "cButtonType": "F",
            "vButtonId": "floorActivityTime",
        },
        {
            "iConfiguredButtonId": 6,
            "vButtonName": "General Meeting",
            "cButtonType": "G",
            "vButtonId": "generalMeetingTime",
        },
        {
            "iConfiguredButtonId": 7,
            "vButtonName": "No Work",
            "cButtonType": "N",
            "vButtonId": "noworkTime",
        },
        {
            "iConfiguredButtonId": 8,
            "vButtonName": "R &amp; D",
            "cButtonType": "R",
            "vButtonId": "rndTime",
        },
    ]
    return configured_buttons


def get_time_duration():
    """Get time duration of the application"""
    return [
        {"applicationId": 1, "name": "Chrome", "timeDuration": 515},
        {"applicationId": 3, "name": "VSCode", "timeDuration": 400},
        {"applicationId": 2, "name": "Android Studio", "timeDuration": 240},
        {"applicationId": 4, "name": "Skype", "timeDuration": 360},
        {"applicationId": 5, "name": "Firefox", "timeDuration": 180},
        {"applicationId": 6, "name": "Safari", "timeDuration": 360},
        {"applicationId": 7, "name": "Netbeans", "timeDuration": 450},
        {"applicationId": 8, "name": "Sublime", "timeDuration": 225},
        {"applicationId": 11, "name": "Explorer", "timeDuration": 515},
        {"applicationId": 12, "name": "Titlebar", "timeDuration": 515},
    ]


def float_to_hms(time_float):
    hours = int(time_float)
    minutes = int((time_float - hours) * 60)
    seconds = int(((time_float - hours) * 60 - minutes) * 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def employee_daily_report_email(user_obj, employee, attendance):
    """Send daily report email"""
    print("\n\nDEBUG: =========== employee_daily_report_email =================\n\n")
    print("\nDEBUG: user_obj", user_obj)
    print("\nDEBUG: employee_obj", employee)
    print("\nDEBUG: attendance_obj", attendance)
    today = datetime.now().date()

    today_meeting_hours = sum(
        request.env["account.analytic.line"]
        .sudo()
        .search(
            [
                ("employee_id", "=", employee.id),
                ("date", "=", today),
                ("task_id.is_meeting_task", "=", True),
            ]
        )
        .mapped("unit_amount")
    )
    print("\nDEBUG: today_meeting_hours", today_meeting_hours)
    today_timesheet_hours = sum(
        request.env["account.analytic.line"]
        .sudo()
        .search(
            [
                ("employee_id", "=", employee.id),
                ("date", "=", today),
                ("task_id.is_meeting_task", "=", False),
            ]
        )
        .mapped("unit_amount")
    )
    print("\nDEBUG: today_timesheet_hours", today_timesheet_hours)
    totalWorkTime = (
        +attendance.estimate_time
        + attendance.interview_time
        + attendance.floor_active_time
        + attendance.general_meeting_time
        + attendance.r_and_d_time
        + today_timesheet_hours
    )
    print("\nDEBUG: totalWorkTime", totalWorkTime)
    totalTime = today_meeting_hours + totalWorkTime + attendance.lunch_time + attendance.break_time + attendance.no_work_time
    print("\nDEBUG: totalTime", totalTime)

    work_time = float_to_hms(totalWorkTime) if totalWorkTime else "00:00:00"

    work_color = "red" if totalWorkTime <= 30600 else "green"

    meeting_time = (
        float_to_hms(today_meeting_hours) if today_meeting_hours else "00:00:00"
    )
    total_time = float_to_hms(totalTime) if totalTime else "00:00:00"

    attendance_data = {
        "today_total_work": work_time,
        "meeting": meeting_time,
        "total_time": total_time,
        "work_color": work_color,
    }
    print("\nDEBUG: attendance_data", attendance_data)
    other_activity = []

    def add_log(start, end, name, total_time):
        """Helper function to add log entry if time is available"""
        if start and end:
            other_activity.append(
                {
                    "name": name,
                    "time": float_to_hms(total_time),
                    "comment": "",
                }
            )

    # Adding relevant logs based on available times
    add_log(
        attendance.lunch_start_time,
        attendance.lunch_end_time,
        "Lunch Break",
        attendance.lunch_time,
    )
    add_log(
        attendance.break_start_time,
        attendance.break_end_time,
        "Break Time",
        attendance.break_time,
    )
    add_log(
        attendance.estimate_start_time,
        attendance.estimate_end_time,
        "Estimate Work",
        attendance.estimate_time,
    )
    add_log(
        attendance.interview_start_time,
        attendance.interview_end_time,
        "Interview",
        attendance.interview_time,
    )
    add_log(
        attendance.floor_start_time,
        attendance.floor_end_time,
        "Floor Active Time",
        attendance.floor_active_time,
    )
    add_log(
        attendance.general_meeting_start_time,
        attendance.general_meeting_end_time,
        "General Meeting",
        attendance.general_meeting_time,
    )
    add_log(
        attendance.no_work_start_time,
        attendance.no_work_end_time,
        "No Work",
        attendance.no_work_time,
    )
    add_log(
        attendance.r_and_d_start_time,
        attendance.r_and_d_end_time,
        "R&D Work",
        attendance.r_and_d_time,
    )

    project_data = []
    timesheet_lines = user_obj.env['account.analytic.line'].sudo().search([
        ('user_id', '=', user_obj.id),
        ('date', '=', today),
        ('task_id', '!=', False),
        ('project_id', '!=', False),
    ])

    merged_data = defaultdict(float)

    for line in timesheet_lines:
        key = (line.project_id.name, line.task_id.name)
        merged_data[key] += line.unit_amount or 0

    for (project_name, task_name), hours in merged_data.items():
        project_data.append({
            'project_name': project_name,
            'task_name': task_name,
            'hours': float_to_hms(hours) or '00:00:00',
        })

    print("\nDEBUG: project_data", project_data)
    # Render QWeb template
    body_html = request.env["ir.qweb"]._render(
        "time_tracker_odoo.employee_daily_report_template",
        values={
            "attendance_data": attendance_data,
            "project_data": project_data,
            "other_activity": other_activity,
            "user_name": user_obj.name if user_obj else "Unknown User",
            "current_time": datetime.now(timezone.utc).strftime(
                "%a, %b %d, %H:%M:%S GMT +05:30 %Y"
            ),
        },
    )

    request.env["mail.mail"].sudo().create(
        {
            "author_id": request.env.user.partner_id.id,
            "email_from": "noreply.tintong@gmail.com",
            "email_to": request.env.user.email,
            "subject": "Time Tracking Report",
            "body_html": body_html,
        }
    ).send()


def get_nowork(attendance, employee):
    """Get no work time"""
    print("\n\nDEBUG: =========== get_nowork =================")

    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    end_of_week = start_of_week + timedelta(days=6)  # Sunday

    print("\nDEBUG: Start of week", start_of_week)
    print("\nDEBUG: End of week", end_of_week)

    today_timesheet_hours = sum(
        request.env["account.analytic.line"]
        .sudo()
        .search(
            [
                ("employee_id", "=", employee.id),
                ("date", "=", today),
                ("task_id.is_meeting_task", "=", False),
            ]
        )
        .mapped("unit_amount")
    )
    print("\nDEBUG: Today timesheet hours", today_timesheet_hours)

    today_meeting_hours = sum(
        request.env["account.analytic.line"]
        .sudo()
        .search(
            [
                ("employee_id", "=", employee.id),
                ("date", "=", today),
                ("task_id.is_meeting_task", "=", True),
            ]
        )
        .mapped("unit_amount")
    )
    print("\nDEBUG: Today meeting hours", today_meeting_hours)

    weekly_timesheet_hours = sum(
        request.env["account.analytic.line"]
        .sudo()
        .search(
            [
                ("employee_id", "=", employee.id),
                ("date", ">=", start_of_week),
                ("date", "<=", end_of_week),
            ]
        )
        .mapped("unit_amount")
    )
    print("\nDEBUG: Weekly timesheet hours", weekly_timesheet_hours)

    totalWorkTime = (
        +attendance.estimate_time * 3600
        + attendance.interview_time * 3600
        + attendance.floor_active_time * 3600
        + attendance.general_meeting_time * 3600
        + attendance.no_work_time * 3600
        + attendance.r_and_d_time * 3600
    )

    # Get remaining weekly hours of the employee
    weeklyTotalHours = get_remaining_weekly_hours(employee)

    return {
        "lunchTime": int(attendance.lunch_time * 3600),
        "breakTime": int(attendance.break_time * 3600),
        "estimationTime": int(attendance.estimate_time * 3600),
        "interviewTime": int(attendance.interview_time * 3600),
        "floorActivityTime": int(attendance.floor_active_time * 3600),
        "generalMeetingTime": int(attendance.general_meeting_time * 3600),
        "noWorkTime": int(attendance.no_work_time * 3600),
        "rndTime": int(attendance.r_and_d_time * 3600),
        "totalTime": int(today_meeting_hours * 3600)
        + int(totalWorkTime)
        + int(attendance.lunch_time * 3600)
        + int(attendance.break_time * 3600)
        + int(today_timesheet_hours * 3600),
        "totalWorkTime": int(totalWorkTime) + int(today_timesheet_hours * 3600),
        "weeklyHours": {
            "weeklyTotalHours": int(weeklyTotalHours * 3600),
            "weeklySpentHours": int(totalWorkTime) + int(weekly_timesheet_hours * 3600),
        },
        "totalMeetTime": int(today_meeting_hours * 3600),
        "workActive": "false",
        "meetActive": "false",
        "lunchActive": "true" if attendance.last_activity_type == "L" else "false",
        "breakActive": "true" if attendance.last_activity_type == "B" else "false",
        "estimationActive": "true" if attendance.last_activity_type == "E" else "false",
        "interviewActive": "true" if attendance.last_activity_type == "I" else "false",
        "floorActivityActive": (
            "true" if attendance.last_activity_type == "F" else "false"
        ),
        "generalMeetingActive": (
            "true" if attendance.last_activity_type == "G" else "false"
        ),
        "noWorkActive": "true" if attendance.last_activity_type == "N" else "false",
        "rndActive": "true" if attendance.last_activity_type == "R" else "false",
        "totalActive": "true",
        "comment": "",
        "setWorkActive": False,
        "setMeetActive": False,
        "empCode": employee.emp_code,
    }


def seconds_to_time(seconds):
    """Convert total seconds into HH:MM:SS format"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"


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


def get_user_employee(user):
    employee = (
        request.env["hr.employee"]
        .sudo()
        .search(
            [
                ("user_id", "=", user.id),
            ]
        )
    )
    return employee


def get_remaining_weekly_hours(employee):
    print("\n\n\n*********** get_remaining_weekly_hours ************ \n\n")
    """Calculate dynamically remaining weekly hours based on current day"""
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())  # Get Monday
    end_of_week = start_of_week + timedelta(days=6)  # Get Sunday

    # Get first check-in of this week
    checkins = (
        request.env["hr.attendance"]
        .sudo()
        .search(
            [
                ("employee_id", "=", employee.id),
                ("check_in", ">=", start_of_week),
                ("check_in", "<=", end_of_week),
            ],
            order="check_in asc",
            limit=1,
        )
    )

    if not checkins:
        print("No check-ins this week.")
        return 0

    first_checkin_date = checkins.check_in.date()
    print(f"DEBUG: First check-in this week: {first_checkin_date}")

    # Get working day weekdays from employee calendar
    working_days = set(employee.resource_calendar_id.attendance_ids.mapped("dayofweek"))

    # Count valid working days from first check-in date to Sunday
    total_days = 0
    for i in range((end_of_week - first_checkin_date).days + 1):
        day = first_checkin_date + timedelta(days=i)
        if str(day.weekday()) in working_days:
            total_days += 1

    print(
        f"DEBUG: Working days from {first_checkin_date} to {end_of_week}: {total_days}"
    )

    weekly_hours = total_days * employee.resource_calendar_id.hours_per_day

    # Fetch approved leave hours within the week
    leave_hours = sum(
        request.env["hr.leave"]
        .sudo()
        .search(
            [
                ("employee_id", "=", employee.id),
                ("state", "=", "validate"),
                ("date_from", ">=", start_of_week),
                ("date_to", "<=", end_of_week),
            ]
        )
        .mapped("number_of_hours")
    )
    print("DEBUG: leave_hours", leave_hours)

    # Fetch public holidays within the week
    holidays = (
        request.env["resource.calendar.leaves"]
        .sudo()
        .search(
            [
                ("date_from", ">=", start_of_week),
                ("date_to", "<=", end_of_week),
                ("resource_id", "=", False),
            ]
        )
    )
    print("DEBUG: holidays", holidays)
    print("Holidays", holidays.name)
    holiday_hours = sum(holidays.holiday_id.mapped("number_of_hours"))
    print("DEBUG: holiday_hours", holiday_hours)

    mandatory_day = (
        request.env["hr.leave.mandatory.day"]
        .sudo()
        .search(
            [
                ("start_date", ">=", start_of_week),
                ("end_date", "<=", end_of_week),
            ]
        )
    )
    print("DEBUG: mandatory_day", mandatory_day.resource_calendar_id)
    mandatory_hours = (
        mandatory_day.resource_calendar_id.hours_per_day if mandatory_day else 0
    )
    print("DEBUG: mandatory_hours", mandatory_hours)

    weekly_work_hours = weekly_hours - leave_hours - holiday_hours + mandatory_hours
    print("DEBUG: weekly_work_hours", weekly_work_hours)
    print("\n\n\n*********** get_remaining_weekly_hours End ************ \n\n")
    return max(weekly_work_hours, 0)


# def get_employee_image_url(employee_id):
#     """Return the employee's image URL."""
#     base_url = request.env["ir.config_parameter"].sudo().get_param("web.base.url")
#     # return f"{base_url}/web/image?model=hr.employee&id={employee_id}&field=image_128"
#     return f"https://img.icons8.com/ios-filled/50/000000/user.png"


def get_employee_image_url(employee_id):

    print("\n\n\n*********** get_employee_image ************ \n\n")
    print("employee_id", employee_id)
    if not employee_id.image_128:
        return False

    try:
        # Decode base64 image
        image_data = base64.b64decode(employee_id.image_128)
        image = Image.open(io.BytesIO(image_data))

        # Convert to PNG
        img_io = io.BytesIO()
        image.save(img_io, format="PNG")
        img_io.seek(0)

        png_base64 = base64.b64encode(img_io.read()).decode("utf-8")
        attachment_name = f"employee_{employee_id.id}.png"

        Attachment = employee_id.env["ir.attachment"]
        attachment = Attachment.sudo().search(
            [
                ("res_model", "=", "hr.employee"),
                ("res_id", "=", employee_id.id),
                ("name", "=", attachment_name),
            ],
            limit=1,
        )

        if not attachment:
            attachment = Attachment.sudo().create(
                {
                    "name": attachment_name,
                    "type": "binary",
                    "datas": png_base64,
                    "mimetype": "image/png",
                    "res_model": "hr.employee",
                    "res_id": employee_id.id,
                    "public": True,
                }
            )

        base_url = (
            employee_id.env["ir.config_parameter"].sudo().get_param("web.base.url")
        )
        return f"{base_url}/web/content/{attachment.id}/{attachment_name}"

    except (base64.binascii.Error, UnidentifiedImageError) as e:
        # Log or handle the error, fallback to default image or return False
        _logger.warning(f"Invalid image for employee {employee_id.id}: {e}")
        return f"https://img.icons8.com/ios-filled/50/000000/user.png"


def _get_project_details(userId):
    """Get project details"""
    print("\nDEBUG: *************_get_project_details************")
    userId = int(userId)

    # Find all tasks assigned to the user
    tasks = (
        request.env["project.task"]
        .sudo()
        .search([("user_ids", "in", [userId]), ("state", "!=", "1_done")])
    )

    # Get unique project IDs from these tasks
    project_ids = list(set(tasks.mapped("project_id.id")))

    # Find projects related to the user's tasks
    project_list = request.env["project.project"].sudo().browse(project_ids)


    list_task = [
        {
            "pdtid": "0",
            "work_time_spent": 0,
            "meet_time_spent": 0,
            "pid": str(project.id),
            "projectName": project.name,
            "pname": project.name,
            "active_time": "0",
            "active_type": None,
            "unassigned": "false" if project.allocated_hours else "true",
            "hours": str(project.allocated_hours),
            "estimatedHours": str(project.allocated_hours),
            "tiIsAccountabilityReportVisible": 0,  # 0 Means [Show 'Add New Task' Button] 1 Means [Hide 'Add New Task' Button]
            "workTypeActive": "true",
            "meetTypeActive": "false",
            "actual": 0,
            "vStatus": [stage.name for stage in request.env['project.task.type'].sudo().search([('project_ids', '=', project.id)])],
            "project_task": [
                {
                    "iProjectTaskId": task.id,
                    "vTask": f"({dict(task._fields['task_type'].selection).get(task.task_type)}) {task.name}",
                    "iTimeSpent": int(task.effective_hours * 3600),
                    "tiIsActive": 1 if task.is_running_tt else 0,
                    "vMilestone": task.milestone_id.name if task.milestone_id else "Milestone",
                    "vModule": "Manual" if not task.module_id else task.module_id.name,
                    "iEstimatedTime": int(task.allocated_hours * 3600),
                    "tiIsComplete": (
                        0
                        if task.stage_id and task.stage_id.name.lower() == "done"
                        else 1
                    ),
                    "iProjectId": str(task.project_id.id),
                    "iUserId": userId,
                }
                for task in tasks.filtered(lambda t: t.project_id.id == project.id)
            ],
        }
        for project in project_list
    ]

    print("DEBUG: project_details", list_task)
    return list_task


class AuthApiController(http.Controller):

    @http.route("/oauth/login", type="http", auth="none", methods=["POST"], csrf=False)
    def api_login(self, **kwargs):
        """Authenticate user and return an API key"""
        print("\n\n\nDEBUG: ********* api_login *********")

        db = request.env.cr.dbname
        email = kwargs.get("vEmailId")
        password = kwargs.get("vPassword")

        if not email or not password:
            return Response(
                json.dumps(
                    {
                        "responseCode": "400",
                        "responseMessage": "Email and password are required",
                    }
                ),
                content_type="application/json",
                status=400,
            )

        try:
            # Authenticate user
            uid = request.env["res.users"].sudo().authenticate(db, email, password, {})

            if not uid:
                return {"status": "error", "message": "Invalid credentials"}

            # Fetch user data
            user = request.env["res.users"].sudo().browse(uid)

            # Check if an API key already exists for the user
            existing_api_key = (
                request.env["auth.api.key"]
                .sudo()
                .search([("user_id", "=", user.id)], limit=1)
            )

            if existing_api_key:
                api_key = existing_api_key.key  # Use existing key
            else:
                # Generate a new API key
                api_key = secrets.token_urlsafe(32)
                request.env["auth.api.key"].sudo().create(
                    {
                        "name": f"API Key for {user.name}",
                        "key": api_key,
                        "user_id": user.id,
                    }
                )

            print(f"DEBUG: api_key: {api_key}")

            """ ********* Employee Check In. ********* """
            employee = get_user_employee(user)
            today = datetime.now().date()
            attendance = (
                request.env["hr.attendance"]
                .sudo()
                .search(
                    [
                        ("employee_id", "=", employee.id),
                        ("check_in", ">=", today.strftime("%Y-%m-%d 00:00:00")),
                        ("check_in", "<=", today.strftime("%Y-%m-%d 23:59:59")),
                    ],
                    limit=1,
                )
            )

            print(f"DEBUG: ========> attendance ==========> : {attendance}")

            if not attendance:
                print(f"DEBUG: Create attendance")
                attendance = (
                    request.env["hr.attendance"]
                    .sudo()
                    .create(
                        {
                            "employee_id": employee.id,
                        }
                    )
                )

            print(f"DEBUG: Image Url: {get_employee_image_url(employee)}")
            responseData = {
                "iUserId": user.id,
                "iScreenShotPerHour": int(0.1),
                "vFirstName": user.partner_id.name or "",
                "vLastName": "",
                "vEmailId": user.email or "",
                "vAuthKey": api_key,
                "vDesignationName": employee.job_id.name if employee.job_id else "",
                "tLunchStart": "01:20 PM",
                "tLunchEnd": "01:40 PM",
                "vProfileImage": get_employee_image_url(employee),
                "configured_buttons": configured_buttons(),
                "listProject": _get_project_details(user.id),
                "nowork": get_nowork(attendance, employee),
                "timeDuration": get_time_duration(),
            }

            data = {
                "responseCode": 200,
                "responseMessage": "Login successfully done",
                "responseData": responseData,
            }
            # print("DEBUG: data: ", json.dumps(data, indent=4))
            print("\n\n\n")
            return Response(
                json.dumps(data),
                content_type="application/json",
                status=200,
            )

        except Exception as e:
            data = {
                "responseCode": 400,
                "responseMessage": "User Not Found.",
                "responseData": [],
            }
            return Response(
                json.dumps(data),
                content_type="application/json",
                status=400,
            )

    @http.route(
        "/oauth/get-applications",
        type="http",
        auth="api_key",
        methods=["GET"],
        csrf=False,
    )
    def get_applications(self, **kwargs):
        """Authenticate user and return an API key"""
        print("\n\nDEBUG: *********get_applications*********")
        print("DEBUG: kwargs", kwargs)
        # Same response retunred in postman
        data = {
            "responseCode": 200,
            "responseMessage": "applications successfully done",
            "responseData": [],
        }

        return Response(
            json.dumps(data),
            content_type="application/json",
            status=200,
        )

    @http.route(
        "/oauth/signout", type="http", auth="api_key", methods=["POST"], csrf=False
    )
    def signout(self, **kwargs):
        """Authenticate user and return an API key"""
        print("\n\n\n********* signout api call *********")

        user_obj = get_authenticated_user()
        print("\nDEBUG: user_obj: ", user_obj)

        employee = get_user_employee(user_obj)
        print("\nDEBUG: employee: ", employee)

        today = datetime.now().date()
        attendance = (
            request.env["hr.attendance"]
            .sudo()
            .search(
                [
                    ("employee_id", "=", employee.id),
                    ("check_in", ">=", today.strftime("%Y-%m-%d 00:00:00")),
                    ("check_in", "<=", today.strftime("%Y-%m-%d 23:59:59")),
                ],
                limit=1,
            )
        )
        print("\nDEBUG: attendance: ", attendance)

        if not attendance:
            data = {
                "responseCode": 400,
                "responseMessage": "Employee is not checked in.",
                "responseData": [],
            }

            return Response(
                json.dumps(data),
                content_type="application/json",
                status=200,
            )

        attendance.write(
            {
                "check_out": datetime.now(),
            }
        )

        # API response
        data = {
            "responseCode": 200,
            "responseMessage": "Signout successfully done",
            "responseData": [],
        }
        if employee:
            employee_daily_report_email(user_obj, employee, attendance)
        print("\n\n\n")
        return Response(
            json.dumps(data),
            content_type="application/json",
            status=200,
        )

    @http.route(
        "/oauth/refresh", type="http", auth="api_key", methods=["GET"], csrf=False
    )
    def refresh(self, **kwargs):
        """Authenticate user and return an API key"""
        print(
            "\n\nDEBUG: ===================== refresh api call =====================\n\n"
        )

        update_traker_value = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("time_tracker_odoo.update_traker")
        )

        headers = request.httprequest.headers
        auth_header = headers.get("Authorization")
        api_key = auth_header.split(" ")[1]

        user = get_authenticated_user()
        print("\nDEBUG: user obj", user)

        employee = get_user_employee(user)
        print("\nDEBUG: employee obj", employee)

        task_update = (
            request.env["project.task"]
            .sudo()
            .search([("user_ids", "=", user.id), ("is_running_tt", "=", True)])
        )
        print("\nDEBUG: task_update obj- is_running_tt", task_update)
        print("\nDEBUG: update_traker_value ", update_traker_value)

        if task_update and update_traker_value is False:
            with request.env.cr.savepoint():

                # Fetch the last updated timesheet entry
                last_timesheet = (
                    request.env["account.analytic.line"]
                    .sudo()
                    .search(
                        [
                            ("task_id", "=", task_update.id),
                            ("employee_id", "=", employee.id),
                        ],
                        order="write_date desc",
                        limit=1,
                    )
                )
                last_timesheet.write(
                    {
                        "end_time": datetime.now(),
                    }
                )
                print("\nDEBUG: last_timesheet obj", last_timesheet)

        today = datetime.now().date()
        attendance = (
            request.env["hr.attendance"]
            .sudo()
            .search(
                [
                    ("employee_id", "=", employee.id),
                    ("check_in", ">=", today.strftime("%Y-%m-%d 00:00:00")),
                    ("check_in", "<=", today.strftime("%Y-%m-%d 23:59:59")),
                ],
                limit=1,
            )
        )

        print("\nDEBUG: attendance obj", attendance)

        responseData = {
            "iUserId": user.id,
            "iScreenShotPerHour": int(0.1),
            "vFirstName": user.partner_id.name or "",
            "vLastName": "",
            "vEmailId": user.email or "",
            "vAuthKey": api_key,
            "vDesignationName": employee.job_id.name if employee.job_id else "",
            "tLunchStart": "01:20 PM",
            "tLunchEnd": "01:40 PM",
            "vProfileImage": get_employee_image_url(employee),
            "configured_buttons": configured_buttons(),
            "listProject": _get_project_details(user.id),
            "nowork": get_nowork(attendance, employee),
            "timeDuration": get_time_duration(),
        }

        # print(
        #     "\n ******* DEBUG: responseData: ******* \n",
        #     json.dumps(responseData, indent=4),
        # )

        # if task_update and update_traker_value == False:
        #     with request.env.cr.savepoint():

        #         # Fetch the last updated timesheet entry
        #         last_timesheet = request.env['account.analytic.line'].sudo().search(
        #             [('task_id','=',task_update.id),('employee_id', '=', employee.id)],
        #             order="write_date desc", limit=1
        #         )
        #         last_timesheet.write({
        #             'start_time': datetime.now(),
        #         })
        #         # request.env.cr.commit()
        #         print("DEBUG: last_timesheet obj", last_timesheet)

        data = {
            "responseCode": 200,
            "responseMessage": "Session refreshed successfully",
            "responseData": responseData,
        }
        print("\n\n\n")
        request.env["ir.config_parameter"].sudo().set_param(
            "time_tracker_odoo.update_traker", False
        )
        return Response(
            json.dumps(data),
            content_type="application/json",
            status=200,
        )

    @http.route(
        "/general-task/work-report",
        type="http",
        auth="api_key",
        methods=["POST"],
        csrf=False,
    )
    def work_report(self, **kwargs):
        print(
            "\n\n ===================== work_report api call =====================\n\n"
        )

        user = get_authenticated_user()
        employee = get_user_employee(user)
        today = datetime.now().date()

        attendance = (
            request.env["hr.attendance"]
            .sudo()
            .search(
                [
                    ("employee_id", "=", employee.id),
                    ("check_in", ">=", today.strftime("%Y-%m-%d 00:00:00")),
                    ("check_in", "<=", today.strftime("%Y-%m-%d 23:59:59")),
                ],
                limit=1,
            )
        )
        print("\nDEBUG: attendance obj", attendance)
        end_time_fields = {
            "I": "interview_end_time",
            "B": "break_end_time",
            "L": "lunch_end_time",
            "G": "general_meeting_end_time",
            "F": "floor_end_time",
            "N": "no_work_end_time",
            "E": "estimate_end_time",
            "R": "r_and_d_end_time",
        }

        print(
            "\nDEBUG: attendance obj last_activity_type", attendance.last_activity_type
        )
        if attendance.last_activity_type:
            last_activity_type = attendance.last_activity_type
            if attendance.last_activity_type in end_time_fields:
                attendance.write(
                    {
                        end_time_fields[last_activity_type]: datetime.now(),
                        "last_activity_type": False,
                    }
                )

        current_task = (
            request.env["project.task"]
            .sudo()
            .search([("user_ids", "=", user.id), ("is_running_tt", "=", True)])
        )
        print("\nDEBUG: current_task obj", current_task)
        if current_task:
            current_ts = (
                request.env["account.analytic.line"]
                .sudo()
                .search(
                    [
                        ("task_id", "=", current_task.id),
                        ("employee_id", "=", employee.id),
                        ("date", "=", today),
                    ],
                    order="write_date desc",
                    limit=1,
                )
            )
            print("\nDEBUG: current_ts obj", current_ts)
            if current_ts:
                current_ts.write({"end_time": datetime.now()})
                current_task.write(
                    {"is_running_tt": False, "task_update_from_tt": False}
                )

        logs = []

        def add_log(start, end, task_name, total_time):
            """Helper function to add log entry if time is available"""
            if start and end:

                start_time = fields.Datetime.context_timestamp(request.env.user, start)
                end_time = fields.Datetime.context_timestamp(request.env.user, end)

                logs.append(
                    {
                        "type": "0",
                        "iProjectid": 0,
                        "iProjectTaskid": "0",
                        "iCreatedAt": int(start.timestamp()),
                        "starttime": (
                            start_time.strftime("%H:%M:%S")
                            if start_time
                            else "00:00:00"
                        ),
                        "endingtime": (
                            end_time.strftime("%H:%M:%S") if start_time else "00:00:00"
                        ),
                        "totaltime": float_to_hms(total_time),
                        "project_name": "",
                        "project_tasks": "",
                        "vButtonName": "",
                        "tasks": task_name,
                        "edited_flag": 1,
                        "tiIsCompleted": 0,
                        "notes": "",
                    }
                )

        # Adding relevant logs based on available times
        add_log(attendance.check_in, attendance.check_out, "Log In", 2.5)
        add_log(
            attendance.lunch_start_time,
            attendance.lunch_end_time,
            "Lunch Break",
            attendance.lunch_time,
        )
        add_log(
            attendance.break_start_time,
            attendance.break_end_time,
            "Break Time",
            attendance.break_time,
        )
        add_log(
            attendance.estimate_start_time,
            attendance.estimate_end_time,
            "Estimate Work",
            attendance.estimate_time,
        )
        add_log(
            attendance.interview_start_time,
            attendance.interview_end_time,
            "Interview",
            attendance.interview_time,
        )
        add_log(
            attendance.floor_start_time,
            attendance.floor_end_time,
            "Floor Active Time",
            attendance.floor_active_time,
        )
        add_log(
            attendance.general_meeting_start_time,
            attendance.general_meeting_end_time,
            "General Meeting",
            attendance.general_meeting_time,
        )
        add_log(
            attendance.no_work_start_time,
            attendance.no_work_end_time,
            "No Work",
            attendance.no_work_time,
        )
        add_log(
            attendance.r_and_d_start_time,
            attendance.r_and_d_end_time,
            "R&D Work",
            attendance.r_and_d_time,
        )

        # logs.append({
        #     "type": "1",
        #     "iProjectid": 0,
        #     "iProjectTaskid": "0",
        #     "iCreatedAt": int(attendance.check_in.timestamp()),
        #     "starttime": attendance.check_in.strftime("%H:%M:%S"),
        #     "endingtime": "",
        #     "totaltime": "0",
        #     "project_name": "",
        #     "project_tasks": "",
        #     "vButtonName": "",
        #     "tasks": "Log In",
        #     "edited_flag": 0,
        #     "tiIsCompleted": 0,
        #     "notes": ""
        # })

        # =========================
        # Timesheet Update / Create
        # =========================

        timesheets = (
            request.env["account.analytic.line"]
            .sudo()
            .search(
                [
                    ("employee_id", "=", employee.id),
                    ("date", "=", today),
                ],
            )
        )

        print("\nDEBUG: timesheets obj", timesheets)

        for timesheet in timesheets:
            created_at = (
                int(timesheet.create_date.timestamp()) if timesheet.create_date else 0
            )

            # Convert times to the user's timezone
            user_tz = request.env.user.tz or "UTC"
            start_time = (
                fields.Datetime.context_timestamp(
                    request.env.user, timesheet.start_time
                )
                if timesheet.start_time
                else None
            )
            end_time = (
                fields.Datetime.context_timestamp(request.env.user, timesheet.end_time)
                if timesheet.end_time
                else None
            )

            logs.append(
                {
                    "type": "1",
                    "iProjectid": (
                        timesheet.account_id.id if timesheet.account_id else 0
                    ),
                    "iProjectTaskid": (
                        str(timesheet.task_id.id) if timesheet.task_id else "0"
                    ),
                    "iCreatedAt": created_at,
                    "starttime": (
                        start_time.strftime("%H:%M:%S") if start_time else "00:00:00"
                    ),
                    "endingtime": (
                        end_time.strftime("%H:%M:%S") if end_time else "00:00:00"
                    ),
                    "totaltime": float_to_hms(timesheet.unit_amount),
                    "project_name": (
                        timesheet.account_id.name if timesheet.account_id else ""
                    ),
                    "project_tasks": (
                        timesheet.task_id.name if timesheet.task_id else ""
                    ),
                    "vButtonName": "Test",
                    "tasks": timesheet.name,
                    "edited_flag": 1,
                    "tiIsCompleted": 1,
                    "notes": timesheet.name,
                }
            )

        logs = sorted(logs, key=lambda x: x["iCreatedAt"])

        print("\nDEBUG: logs obj", logs)
        responseData = {"workreport": logs, "nowork": get_nowork(attendance, employee)}

        data = {
            "responseCode": 200,
            "responseMessage": "Report Show successfully",
            "responseData": responseData,
        }
        print(
            "\n\n ===================== work_report api call END =====================\n\n"
        )
        return Response(
            json.dumps(data),
            content_type="application/json",
            status=200,
        )

    @http.route(
        "/oauth/get-server-current-time", type="json", auth="public", methods=["GET"]
    )
    def get_server_current_time(self):
        print("\n\nDEBUG: *********get_server_current_time api call*********\n\n")
        """Return Odoo server's current time, timestamp, and timezone"""

        # Get the server's timezone from Odoo settings (default to UTC)
        user_tz = request.env.user.tz or "UTC"
        timezone = pytz.timezone(user_tz)

        # Get the current time in the user's timezone
        now = datetime.now(timezone)
        formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
        timestamp = int(now.timestamp())

        # API Response
        response = {
            "responseCode": 200,
            "responseMessage": "Success",
            "responseData": {
                "time": formatted_time,
                "timestamp": timestamp,
                "timezone": user_tz,
            },
        }
        return response
