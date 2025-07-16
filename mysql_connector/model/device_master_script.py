import xmlrpc.client
import mysql.connector
from datetime import datetime, date


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

        project_name = ""
        status = False
        device_type = False
        if record.get('vDedicatedProjectName'):
            project_id = models.execute_kw(odoo_db, uid, odoo_password, 'project.project', 'search', [[('name', '=', record.get('vDedicatedProjectName'))]])
            project_name = models.execute_kw(odoo_db, uid, odoo_password, 'project.project', 'read', [project_id], {'fields': ['name']})
            project_name = project_name[0]['name']

        if record.get('tiStatus') == 1:
            status = 'on_floor'
        if record.get('tiStatus') == 2:
            status = 'not_working'
        if record.get('tiStatus') == 3:
            status = 'under_maintenance'
        if record.get('tiStatus') == 4:
            status = 'in_cabin'
        if record.get('tiStatus') == 5:
            status = 'spare'
        if record.get('tiStatus') == 6:
            status = 'sold'

        if record.get('tiDeviceType') == 1:
            device_type = 'iphone'
        if record.get('tiDeviceType') == 2:
            device_type = 'android'
        if record.get('tiDeviceType') == 3:
            device_type = 'watch'

        print("Debug------------------- status ----->", status)
        print("Debug------------------- project_name ----->", project_name)
        print("Debug------------------- device_type ----->", device_type)

        vals = {
            "name": clean_data(record.get("vDeviceName")),
            'tt_id': clean_data(record.get("iDeviceMasterId")),
            'unique_name': clean_data(record.get("vUniqueId")),
            'device_label': clean_data(record.get("vDeviceLabel")),
            'device_type': device_type,
            'serial_number': clean_data(record.get("vSerialNumber")),
            'imei_number': clean_data(record.get("vIMEINumber")),
            'on_floor_date': format_date(record.get("dtOnFloorDate")),
            'os_name': clean_data(record.get("vOsName")),
            'os_version': clean_data(record.get("vOsversion")),
            'cabin_name': clean_data(record.get("vCabinName")),
            'notes': clean_data(record.get("lNotes")),
            'state': status,
            'project_name': project_name,
        }

        # Check if the record already exists in Odoo
        existing_ids = models.execute_kw(
            odoo_db,
            uid,
            odoo_password,
            odoo_model,
            "search",
            [[("tt_id", "=", record["iDeviceMasterId"])]],
        )

        if existing_ids:
            # Update existing record
            models.execute_kw(
                odoo_db, uid, odoo_password, odoo_model, "write", [existing_ids, vals]
            )
            print(f"Updated record {record['vDeviceName']}")
        else:
            # Create new record
            if vals:
                models.execute_kw(
                    odoo_db, uid, odoo_password, odoo_model, "create", [vals]
                )
                print(f"Created new record {record['vDeviceName']}")


def main():
    # Connect to Odoo and MySQL
    models, uid = connect_odoo()
    connection = connect_mysql()

    # Define the table name in MySQL and corresponding model in Odoo
    mysql_table = "device_master"
    odoo_model = "device.management"

    # Fetch data from MySQL
    mysql_data = fetch_mysql_data(connection, mysql_table)

    # Import data into Odoo
    import_data_to_odoo(models, uid, odoo_model, mysql_data)


if __name__ == "__main__":
    main()
