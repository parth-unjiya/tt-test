import xmlrpc.client
import mysql.connector
from datetime import datetime, date

# Odoo connection details
odoo_url = "http://127.0.0.67:6767/xmlrpc/2"
odoo_db = "hrms_db_21_02_25"
odoo_username = "admin"
odoo_password = "admin"


# MySQL connection details
mysql_host = "localhost"
mysql_user = "root"
mysql_password = "Aa@12345678"
mysql_db = "tt_staging_v21"


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
    cursor.execute(f"SELECT * FROM {table_name}")
    result = cursor.fetchall()
    cursor.close()
    print("===============>", result)
    return result


def import_data_to_odoo(models, uid, odoo_model, data):
    """Insert data into Odoo via XML-RPC."""

    # Helper function to replace None with an empty string
    def clean_data(value):
        return value if value is not None else ""

    # Helper function to format date properly
    def format_date(date_value):
        if isinstance(date_value, (datetime, date)):
            return date_value.strftime("%Y-%m-%d")
        return None  # Use None if the date is invalid or None

    for record in data:
        # Extract and format start and end dates
        start_date = format_date(record.get("dStartDate"))
        end_date = format_date(record.get("dEndDate"))

        # Search for the employee using 'tt_id'
        employee_search_domain = [("tt_id", "=", record["iUserId"])]
        employee = models.execute_kw(
            odoo_db,
            uid,
            odoo_password,
            "hr.employee",
            "search_read",
            [employee_search_domain],
            {"fields": ["id", "user_id", "department_id"]},
        )
        if not employee:
            print(f"No employee found for tt_id: {record['iUserId']}")
            continue

        employee_id = employee[0]["id"]
        department_id = employee[0].get("department_id") or False
        user_id = employee[0]["user_id"][0] if employee[0].get("user_id") else False    

        # Get the holiday type ID
        holiday_status_id = models.execute_kw(
            odoo_db,
            uid,
            odoo_password,
            "hr.leave.type",
            "search",
            [[("name", "=", "Paid Time Off")]],
            {"limit": 1},
        )

        # state = 'draft'

        # if record['iStatusMasterId'] == 3:
        #     state = 'confirm'
        # if record['iStatusMasterId'] == 4:
        #     state = 'refuse'
        # if record['iStatusMasterId'] == 5:
        #     state = 'validate'
        # if record['iStatusMasterId'] == 6:
        #     state = 'refuse'

        
        # Define values for the leave record
        vals = {
            "name": clean_data(record["txLeaveReason"]),
            "user_id": user_id,
            "employee_id": employee_id,
            "department_id": department_id[0],
            "holiday_status_id": holiday_status_id[0] if holiday_status_id else False,
            "request_date_from": start_date,
            "request_date_to": end_date,
            "number_of_days_display": clean_data(record["siTotalDays"]),
            "tt_id": clean_data(record["iLeaveId"]),
            # "state": state,
        }
        print(vals)

        # Check for existing records with the same 'tt_id' to avoid duplicates
        existing_ids = models.execute_kw(
            odoo_db,
            uid,
            odoo_password,
            odoo_model,
            "search",
            [[("tt_id", "=", record.get("iLeaveId"))]],
        )

        # # Check for overlapping leaves for the employee in the same date range
        overlap_domain = [
            ("employee_id", "=", employee_id),
            ("request_date_from", "<=", end_date),
            ("request_date_to", ">=", start_date),
            (
                "holiday_status_id",
                "=",
                holiday_status_id[0] if holiday_status_id else False,
            ),
        ]
        overlapping_leaves = models.execute_kw(
            odoo_db, uid, odoo_password, odoo_model, "search", [overlap_domain]
        )

        if overlapping_leaves:
            print(
                f"Skipping record {record.get('iLeaveId')} due to overlapping leave for employee."
            )
            continue

        if existing_ids:
            # Update existing record
            models.execute_kw(
                odoo_db, uid, odoo_password, odoo_model, "write", [existing_ids, vals]
            )
            print(f"Updated record {record.get('iLeaveId')}")
        else:
            # Create new record
            models.execute_kw(odoo_db, uid, odoo_password, odoo_model, "create", [vals])
            print(f"Created new record {record.get('iLeaveId')}")


def main():
    # Connect to Odoo and MySQL
    models, uid = connect_odoo()
    connection = connect_mysql()

    # Define the table name in MySQL and corresponding model in Odoo
    mysql_table = "leave_master"
    odoo_model = "hr.leave"

    # Fetch data from MySQL
    mysql_data = fetch_mysql_data(connection, mysql_table)

    # Import data into Odoo
    import_data_to_odoo(models, uid, odoo_model, mysql_data)


if __name__ == "__main__":
    main()
