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

        user_id = False
        if clean_data(record["iUserId"]):
            user_id = models.execute_kw(
                odoo_db,
                uid,
                odoo_password,
                'res.users',
                'search',
                [[('tt_id', '=', clean_data(record["iUserId"]))]]
            )

        print("\nDebug--------------------------- user ---------------------->", user_id)

        resource_project_id = False
        if clean_data(record["iProjectId"]):
            resource_project_id = models.execute_kw(
                odoo_db,
                uid,
                odoo_password,
                "project.project",
                "search",
                [[("tt_id", "=", clean_data(record["iProjectId"]))]],
            )

        print("\nDebug------------------- resource ------------------>", resource_project_id)

        status = False
        if clean_data(record["iStatusMasterId"]) == 28:
            status = 'confirmed'
        if clean_data(record["iStatusMasterId"]) == 29:
            status = 'approve'
        if clean_data(record["iStatusMasterId"]) == 30:
            status = 'reject'

        print("\nDebug ------------------------ status ------------------>", status)
        resource_id = models.execute_kw(
            odoo_db,
            uid,
            odoo_password,
            'resource.resource',
            'search',
            [[('user_id.tt_id', '=', clean_data(record["iUserId"]))]]
        )


        print("\nDebug ------------------------ resource_id ------------------>", resource_id)

        # Create a new record
        vals = {
            "tt_id": clean_data(record["iResourceMasterId"]),
            'project_id': resource_project_id[0] if resource_project_id else False,
            'user_id': user_id[0] if user_id else False,
            'resource_id': resource_id[0] if resource_id else False,
            'allocation_hours': clean_numeric(record["iResourceHoursPerDay"]),
            'start_date': format_date(record["dtRequestedStartDate"]),
            'end_date': format_date(record["dtRequestedEndDate"]),
            'state': status if status else False,

        }

        print("===>vals", vals)
        # input("Press Enter to continue...")

        # Check if the record already exists in Odoo
        existing_ids = models.execute_kw(
            odoo_db,
            uid,
            odoo_password,
            odoo_model,
            "search",
            [[("tt_id", "=", record.get("iResourceMasterId"))]],
        )

        if existing_ids:
            # Update existing record
            models.execute_kw(
                odoo_db, uid, odoo_password, odoo_model, "write", [existing_ids, vals]
            )
            print(f"Updated record {record.get('iResourceMasterId')}")
        else:
            # Create new record
            models.execute_kw(odoo_db, uid, odoo_password, odoo_model, "create", [vals])
            print(f"Created new record {record.get('iResourceMasterId')}")




def main():
    # Connect to Odoo and MySQL
    models, uid = connect_odoo()
    connection = connect_mysql()

    # Define the table name in MySQL and corresponding model in Odoo
    mysql_table = "resource_master"
    odoo_model = "resource.allocation"

    # Fetch data from MySQL
    mysql_data = fetch_mysql_data(connection, mysql_table)

    # Import data into Odoo
    import_data_to_odoo(models, uid, odoo_model, mysql_data)


if __name__ == "__main__":
    main()
