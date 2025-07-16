import xmlrpc.client
import mysql.connector
from datetime import datetime, date, timedelta, timezone

from pprint import pprint
from collections import defaultdict


# Odoo connection details
odoo_url = "http://127.0.0.67:8069/xmlrpc/2"
odoo_db = "internal_erp_24_feb_25"
odoo_username = "admin"
odoo_password = "admin"


# MySQL connection details
mysql_host = "localhost"
mysql_user = "root"
mysql_password = "ur48x"
mysql_db = "tingtong_v2"


def connect_odoo():
    """Connect to Odoo via XML-RPC and return models object."""
    common = xmlrpc.client.ServerProxy("{}/common".format(odoo_url))
    uid = common.authenticate(odoo_db, odoo_username, odoo_password, {})

    if uid:
        models = xmlrpc.client.ServerProxy("{}/object".format(odoo_url))
        print("Connected to Odoo successfully!----->", models)
        return models, uid
    else:
        raise Exception("Failed to authenticate with Odoo")


def connect_mysql():
    """Connect to MySQL and return the connection object."""
    try:
        connection = mysql.connector.connect(
            host=mysql_host,
            user=mysql_user,
            password=mysql_password,
            database=mysql_db,
            port=3306,
        )
        print("Connected to MySQL successfully!-------->", connection)
        return connection
    except mysql.connector.Error as err:
        raise Exception(f"Error connecting to MySQL: {err}")


def fetch_mysql_data(connection, table_name):
    """Fetch data from a specific MySQL table."""
    cursor = connection.cursor(dictionary=True)

    # query = f"""
    #     SELECT * 
    #     FROM {table_name} 
    #     WHERE iUserId = %s AND eActivity = %s
    #     ORDER BY iUserId, dtDate, iCreatedAt
    # """
    # cursor.execute(query, (466, 'W'))

    cursor.execute(
        f"SELECT * FROM {table_name} ORDER BY iUserId, dtDate, iCreatedAt;" # LIMIT 1000 OFFSET 15;
    )
    result = cursor.fetchall()
    cursor.close()

    grouped_logs = defaultdict(list)

    for row in result:
        key = (row['iUserId'], row['dtDate'])
        # key = row["iUserId"]
        grouped_logs[key].append(row)

    structured_logs = [
        {
            "iUserId": user_id,
            "dtDate": date,
            "logs": sorted(log_entries, key=lambda x: x["iCreatedAt"]),
        }
        for (user_id, date), log_entries in grouped_logs.items()
    ]
    data = filter_logs_keep_only_first_login_and_last_logout(structured_logs)
    return data


def filter_logs_keep_only_first_login_and_last_logout(structured_logs):
    """
    For each day's log:
    - Keep the first '1' (login) with the smallest iCreatedAt
    - Keep all other activity logs (e.g., 'W', 'L', 'M', etc.)
    - Keep the last '0' (logout) with the largest iCreatedAt
    - Add totalSecond to each log: difference with next iCreatedAt
    """
    filtered_data = []

    for entry in structured_logs:
        logs = sorted(entry["logs"], key=lambda x: x["iCreatedAt"])  # sort just in case

        # Get all logins and logouts
        login_logs = [log for log in logs if log["eActivity"] == "1"]
        logout_logs = [log for log in logs if log["eActivity"] == "0"]
        other_logs = [log for log in logs if log["eActivity"] not in ("0", "1")]

        # Find the earliest login and latest logout
        login_entry = min(login_logs, key=lambda x: x["iCreatedAt"]) if login_logs else None
        logout_entry = max(logout_logs, key=lambda x: x["iCreatedAt"]) if logout_logs else None

        # Build the filtered log list
        filtered_logs = []
        if login_entry:
            filtered_logs.append(login_entry)
        filtered_logs.extend(other_logs)
        if logout_entry:
            filtered_logs.append(logout_entry)

        # Sort again to apply time difference correctly
        # filtered_logs.sort(key=lambda x: x["iCreatedAt"])

        # Add totalSecond based on next log
        for i in range(len(filtered_logs)):
            current = filtered_logs[i]
            if i < len(filtered_logs) - 1:
                next_log = filtered_logs[i + 1]
                current["totalSecond"] = next_log["iCreatedAt"] - current["iCreatedAt"]
                current["nextCreatedAt"] = next_log["iCreatedAt"]
            else:
                current["totalSecond"] = 0
                current["nextCreatedAt"] = 0

        filtered_data.append({
            "iUserId": entry["iUserId"],
            "dtDate": entry["dtDate"],
            "logs": filtered_logs,
        })

        # print("\n\n\n ============================= \n\n")
        # print(filtered_data)
        # print("\n\n\n ***************************** \n\n")

    return filtered_data



def seconds_to_float_hours(seconds):
    return round(seconds / 3600, 2)

def import_data_to_odoo(models, uid, odoo_model, data):    
    """
    Imports structured activity logs to Odoo using the provided model interface.
    """
    count = 1
    activity_field_map = {
        "L": ("lunch_start_time", "lunch_end_time"),
        "B": ("break_start_time", "break_end_time"),
        "E": ("estimate_start_time", "estimate_end_time"),
        "I": ("interview_start_time", "interview_end_time"),
        "F": ("floor_start_time", "floor_end_time"),
        "G": ("general_meeting_start_time", "general_meeting_end_time"),
        "N": ("no_work_start_time", "no_work_end_time"),
        "R": ("r_and_d_start_time", "r_and_d_end_time"),
    }

    for entry in data:
        print(f"\n\nDEBUG: Processing Entry #{count} for User ID {entry['iUserId']} on {entry['dtDate']}")
        # print(f"\n\nDEBUG: Logs: {entry['logs']}\n\n")
        activity_totals = defaultdict(int)
        checkin_time = None
        checkout_time = None
        attendance_id = None
        iUserId = entry["iUserId"]

        user_id = models.execute_kw(
            odoo_db,
            uid,
            odoo_password,
            "res.users",
            "search",
            [[("tt_id", "=", int(iUserId))]],
        )
        if not user_id:
            print("\nUser not found for tt_id", iUserId)
            continue

        employee_id = models.execute_kw(
            odoo_db,
            uid,
            odoo_password,
            "hr.employee",
            "search",
            [[("user_id", "=", user_id[0])]],
        )
        if not employee_id:
            print("Employee not found for user_id", user_id[0])
            continue

        for log in entry["logs"]:
            
            activity = log["eActivity"]
            iCreatedAt = log.get("iCreatedAt", 0)
            nextCreatedAt = log.get("nextCreatedAt", 0)
            
            if activity == "1":
                # Create check-in
                checkin = datetime.fromtimestamp(iCreatedAt, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                checkin_time = checkin

                # Search if attendance already exists with same check_in and employee_id
                existing_attendance = models.execute_kw(
                    odoo_db,
                    uid,
                    odoo_password,
                    odoo_model,
                    "search",
                    [[
                        ("employee_id", "=", int(employee_id[0])),
                        ("check_in", "=", checkin)
                    ]]
                )

                if existing_attendance:
                    print(f"⏩ Attendance already exists for check-in {checkin}, skipping creation.")
                    attendance_id = existing_attendance[0]  # Just store to update later
                    continue

                data = {
                    "employee_id": int(employee_id[0]),
                    "check_in": checkin,
                }
                attendance_id = models.execute_kw(odoo_db, uid, odoo_password, odoo_model, "create", [data])
                print(f"⏩ Attendance creation for check-in {checkin}, ID: {attendance_id}")

            elif activity in activity_field_map:
                print("\n Update activity")
                start_field, end_field = activity_field_map[activity]
                print("\n start_field, end_field", start_field, end_field)
                start_time = datetime.fromtimestamp(iCreatedAt, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                end_time = datetime.fromtimestamp(nextCreatedAt, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S') if nextCreatedAt else False
                print("\n start_time, end_time", start_time, end_time)
                update_data = {
                    start_field: start_time,
                }
                if end_time:
                    update_data[end_field] = end_time

                models.execute_kw(
                    odoo_db,
                    uid,
                    odoo_password,
                    odoo_model,
                    "write",
                    [[attendance_id], update_data],
                )
            
            elif activity in ["W", "M"]:
                print("\n **************************************************** \n")
                print("\n📝 Create timesheet entry for activity:", activity)

                # Compute duration in hours
                duration = (nextCreatedAt - iCreatedAt) / 3600.0 if nextCreatedAt and iCreatedAt else 0.0

                # Description based on activity
                description = "Work" if activity == "W" else "Meeting"

                # Convert created timestamp to datetime string
                create_datetime = datetime.fromtimestamp(iCreatedAt, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

                # Get project and task IDs (safe default to None)
                project_id = log.get("iProjectId")
                task_id = log.get("iProjectTaskId")
                print("\n********************** Ptoject ID", project_id)
                print("\n********************** Task ID", task_id)

                if not project_id:
                    print("⚠️ Skipped: Missing project_id")
                    continue

                # Search for project with tt_id
                project = models.execute_kw(
                    odoo_db, uid, odoo_password,
                    'project.project', 'search',
                    [[('tt_id', '=', int(project_id))]]
                )
                print("\n**********************Odoo Project", project)
                if not project:
                    print("⚠️ Skipped: Project not found in Odoo with tt_id =", project_id)
                    continue

                # Step 1: If task_id not provided, create a task
                if not task_id:
                    task_name = f"{description} on {log['dtDate']}"

                    # Check if task with same name already exists in the project
                    existing_task = models.execute_kw(
                        odoo_db,
                        uid,
                        odoo_password,
                        "project.task",
                        "search",
                        [[
                            ("name", "=", task_name),
                            ("project_id", "=", int(project[0])),
                            ("user_ids", "in", [user_id[0]])
                        ]],
                        {"limit": 1}
                    )

                    if existing_task:
                        task_id = existing_task[0]
                        print("ℹ️ Existing Task Found:", task_id)
                    else:
                        task_id = models.execute_kw(
                            odoo_db,
                            uid,
                            odoo_password,
                            "project.task",
                            "create",
                            [{
                                "name": task_name,
                                "project_id": project[0],
                                "user_ids": [(6, 0, [user_id[0]])],
                            }]
                        )
                        print("✅ New Task Created:", task_id)

                else:
                    print("✅ Existing Task Found: if task_id:", task_id)
                    task_id = models.execute_kw(
                        odoo_db, uid, odoo_password,
                        'project.task', 'search',
                        [[
                            ('tt_id', '=', int(task_id)),
                            ('user_ids', 'in', [user_id[0]]),
                            ('project_id', '=', project[0])
                        ]]
                    )
                    if task_id:
                        task_id = task_id[0]
                    else:
                        print("⚠️ Skipped: Task not found in Odoo with tt_id =", task_id)
                        continue
                    print("✅ Existing Task Found: odoo", task_id)


                # Step 2: Check if timesheet already exists (same employee & create_date)
                existing_timesheet = models.execute_kw(
                    odoo_db,
                    uid,
                    odoo_password,
                    "account.analytic.line",
                    "search",
                    [[
                        ("employee_id", "=", int(employee_id[0])),
                        ("tt_id", "=", create_datetime),
                        ("project_id", "=", project[0]),
                        ("task_id", "=", task_id),
                    ]]
                )
                print("🔍 Existing Timesheet:", existing_timesheet)

                # Step 3: Create timesheet only if not already present
                if not existing_timesheet:
                    timesheet_data = {
                        "employee_id": int(employee_id[0]),
                        "user_id": int(user_id[0]),
                        "name": description,
                        "date": log["dtDate"].isoformat() if log.get("dtDate") else False,
                        "unit_amount": round(duration, 2),
                        "create_date": create_datetime,
                        "tt_id": create_datetime,
                        "project_id": project[0],
                        "task_id": task_id,
                    }

                    models.execute_kw(
                        odoo_db,
                        uid,
                        odoo_password,
                        "account.analytic.line",
                        "create",
                        [timesheet_data]
                    )
                    print("✅ Timesheet created")
                print("\n **************************************************** \n")

        # Update check-out
        print("\n check-out")
        checkout = datetime.fromtimestamp(iCreatedAt, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        models.execute_kw(
            odoo_db,
            uid,
            odoo_password,
            odoo_model,
            "write",
            [[attendance_id], {"check_out": checkout if checkout else checkin_time}],
        )

        count += 1

def main():
    # Connect to Odoo and MySQL
    models, uid = connect_odoo()
    connection = connect_mysql()

    # Define the table name in MySQL and corresponding model in Odoo
    mysql_table = "time_tracking_logs"
    odoo_model = "hr.attendance"

    # Fetch data from MySQL
    mysql_data = fetch_mysql_data(connection, mysql_table)

    # Import data into Odoo
    import_data_to_odoo(models, uid, odoo_model, mysql_data)


if __name__ == "__main__":
    main()
