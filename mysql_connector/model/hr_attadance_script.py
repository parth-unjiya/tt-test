import xmlrpc.client
import mysql.connector
from datetime import datetime, date

from typing import Union

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
    print("\n\nDEBUG: Total Records:", len(data))

    def format_date(date_value: Union[datetime, date]) -> str:
        if isinstance(date_value, (datetime, date)):
            return date_value.strftime("%Y-%m-%d %H:%M:%S")
        return False

    for i, record in enumerate(data, start=1):
        employee_id = models.execute_kw(
            odoo_db,
            uid,
            odoo_password,
            "hr.employee",
            "search",
            [[("emp_code", "=", record["vEmpCode"])]],
        )

        print("\n\n employee_id", employee_id)
        
        vals = {
            "employee_id": (
                employee_id[0] if employee_id else ""
            ),  # Set default to an empty string if None
            # "emp_code": (
            #     record.get("vEmpCode") if record.get("vEmpCode") != None else ""
            # ),
            "check_in": format_date(
                record.get("dtPunchIn")
            ),  # Use format_date function to handle record.get('dtPunchIn') if record.get('dtPunchIn') != None else ' ',
            "check_out": format_date(
                record.get("dtPunchOut")
            ),  # Use format_date function to handle daterecord.get('dtPunchOut') if record.get('dtPunchOut') != None else ' ',
            "tt_id": i,  # Add sequence number
            # 'short_name': record.get('vShortName') if record.get('vShortName') != None else ' ',
        }
        print(vals)

        if not vals.get("check_out"):
            print(f"Skipping record {record['vName']} due to missing check_out date")
            continue
        

        # Check if the record already exists in Odoo
        existing_ids = models.execute_kw(
            odoo_db, uid, odoo_password, odoo_model, "search", [[("tt_id", "=", i)]]
        )

        if existing_ids:
            # Update existing record
            models.execute_kw(
                odoo_db, uid, odoo_password, odoo_model, "write", [existing_ids, vals]
            )
            print(f"Updated record {record['vName']}")
        else:
            # Create new record
            if vals:
                models.execute_kw(
                    odoo_db, uid, odoo_password, odoo_model, "create", [vals]
                )
                print(f"Created new record {record['vName']}")


def main():
    # Connect to Odoo and MySQL
    models, uid = connect_odoo()
    connection = connect_mysql()

    # Define the table name in MySQL and corresponding model in Odoo
    mysql_table = "user_daily_punch_time"
    odoo_model = "hr.attendance"

    # Fetch data from MySQL
    mysql_data = fetch_mysql_data(connection, mysql_table)

    # Import data into Odoo
    import_data_to_odoo(models, uid, odoo_model, mysql_data)


if __name__ == "__main__":
    main()
