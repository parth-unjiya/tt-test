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
mysql_db = "my_database"


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
    # print("===============>", result)
    return result


def import_data_to_odoo(models, uid, odoo_model, data):
    """Insert data into Odoo via XML-RPC."""
    print("----->", data)

    # Helper function to replace None with an empty string
    def clean_data(value):
        return value if value is not None else ""

    def clean_numeric(value):
        try:
            return float(value)  # Convert to float
        except (ValueError, TypeError):
            return 0.0

    for record in data:
        def format_date(date_value):
            if isinstance(date_value, (datetime, date)):
                return date_value.strftime("%Y-%m-%d")  # Format the date properly
            return False  # Use None if the date is invalid or None

        assigned_user_id = False
        if record['iAssignedUserId']:
            assigned_user_id = models.execute_kw(
                odoo_db,
                uid,
                odoo_password,
                "res.users",
                "search",
                [
                    [("tt_id", "=", record["iAssignedUserId"])],
                ]
            )

        print("---------------- MYSQL user ----------------->", record["iUserId"])
        user_id = models.execute_kw(
            odoo_db,
            uid,
            odoo_password,
            "res.users",
            "search",
            [
                [("tt_id", "=", clean_data(record["iUserId"]))],
            ]
        )

        print("------------ user_id ------------->", user_id)

        employee_id = False
        if user_id:
            employee_id = models.execute_kw(
                odoo_db,
                uid,
                odoo_password,
                "hr.employee",
                "search_read", [[("user_id", "=", user_id[0])]], {"fields": ["id", "name"]})
        print("------------ employee_id ------------->", employee_id)


        category_id = models.execute_kw(
            odoo_db,
            uid,
            odoo_password,
            "helpdesk.category",
            "search",
            [
                [("tt_id", "=", record["tiTicketCategories"])],
            ]
        )

        if record['iTicketStatusId'] == 0:
            status = 3
        else:
            status = 4

        existing_ids = models.execute_kw(
            odoo_db,
            uid,
            odoo_password,
            "ticket.helpdesk",
            "search",
            [
                [("tt_id", "=", record["iSupportTicketSystemId"])],
            ]
        )


        vals = {
            "name": employee_id[0].get('name') + "'s Ticket" if employee_id else "New Ticket",
            'category_id': category_id[0] if category_id else False,
            'employee_id': employee_id[0].get('id') if employee_id else False,
            "tt_id": clean_data(record["iSupportTicketSystemId"]),
            'description': clean_data(record['vIssueSummary']),
            'start_date': format_date(record['dtDate']),
            'end_date': format_date(record['dtResolveDate']),
            'employee_rating': clean_data(record['iRating']),
            'review': clean_data(record['txRatingComment']),
            'stage_id': status,
            'assigned_user_id': assigned_user_id[0] if assigned_user_id else False,
        }

        print("------------ vals ------------->", vals)

        if existing_ids:
            # Update existing record
            models.execute_kw(
                odoo_db, uid, odoo_password, odoo_model, "write", [existing_ids, vals]
            )
            print(f"Updated record {record.get('iSupportTicketSystemId')}")
        else:
            # Create new record
            models.execute_kw(odoo_db, uid, odoo_password, odoo_model, "create", [vals])
            print(f"Created new record {record.get('iSupportTicketSystemId')}")


def main():
    # Connect to Odoo and MySQL
    models, uid = connect_odoo()
    connection = connect_mysql()

    # Define the table name in MySQL and corresponding model in Odoo
    mysql_table = "support_ticket_system"
    odoo_model = "ticket.helpdesk"

    # Fetch data from MySQL
    mysql_data = fetch_mysql_data(connection, mysql_table)

    # Import data into Odoo
    import_data_to_odoo(models, uid, odoo_model, mysql_data)


if __name__ == "__main__":
    main()
