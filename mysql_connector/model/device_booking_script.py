import xmlrpc.client
import mysql.connector
from datetime import datetime, date, timedelta


# Odoo connection details
odoo_url = "http://localhost:6767/xmlrpc/2"
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
    print("===============>", result)
    return result


def import_data_to_odoo(models, uid, odoo_model, data):
    """Insert data into Odoo via XML-RPC."""
    # print("----->", data)
    for record in data:

        # Check if the record already exists in Odoo
        def clean_data(value):
            return value if value is not None else ''

        def format_date(date_value):
            if isinstance(date_value, (datetime, date)):
                return date_value.strftime("%Y-%m-%d")  # Format the date properly
            return None  # Use None if the date is invalid or None

        def format_datetime(date_value):
            if date_value:
                dt = datetime.utcfromtimestamp(date_value)
                print("Debug------------------ dt ----->", dt)
                formatted = (dt + timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
                print("Debug------------------ formatted ----->", formatted)
                return formatted  # Format the datetime properly
            return False

        user_id = False
        device_id = False
        if record.get("iUserId"):
            user_id = models.execute_kw(
                odoo_db, uid, odoo_password, "res.users", "search", [[("tt_id", "=", record["iUserId"])]]
            )

        if record.get("iDeviceMasterId"):
            device_id = models.execute_kw(
                odoo_db, uid, odoo_password, "device.management", "search", [[("tt_id", "=", record["iDeviceMasterId"])]]
            )

        print("---device_id-->", device_id)
        print("--user_id--->", user_id)

        vals = {
            'tt_id': clean_data(record.get("iDeviceBookingId")),
            'device_id': device_id[0] if device_id else False,
            'occupied_by': user_id[0] if user_id else False,
            'occupied_at': format_datetime(clean_data(record.get("iBookingTime"))),
            'released_at': format_datetime(clean_data(record.get("iReleaseTime"))),
        }

        # Check if the record already exists in Odoo
        existing_ids = models.execute_kw(
            odoo_db,
            uid,
            odoo_password,
            odoo_model,
            "search",
            [[("tt_id", "=", record["iDeviceBookingId"])]],
        )

        if existing_ids:
            # Update existing record
            models.execute_kw(
                odoo_db, uid, odoo_password, odoo_model, "write", [existing_ids, vals]
            )
            print(f"Updated record {record['iDeviceBookingId']}")
        else:
            # Create new record
            if vals:
                models.execute_kw(
                    odoo_db, uid, odoo_password, odoo_model, "create", [vals]
                )
                print(f"Created new record {record['iDeviceBookingId']}")


def main():
    # Connect to Odoo and MySQL
    models, uid = connect_odoo()
    connection = connect_mysql()

    # Define the table name in MySQL and corresponding model in Odoo
    mysql_table = "device_booking"
    odoo_model = "device.line"

    # Fetch data from MySQL
    mysql_data = fetch_mysql_data(connection, mysql_table)

    # Import data into Odoo
    import_data_to_odoo(models, uid, odoo_model, mysql_data)


if __name__ == "__main__":
    main()
