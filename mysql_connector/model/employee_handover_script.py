import xmlrpc.client
import mysql.connector

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

    def clean_data(value):
        return value if value is not None else ""

    for record in data:
        employee_id = models.execute_kw(
            odoo_db,
            uid,
            odoo_password,
            "hr.employee",
            "search",
            [[("tt_id", "=", record["iUserId"])]],
        )
        approver_id = models.execute_kw(
            odoo_db,
            uid,
            odoo_password,
            "hr.employee",
            "search",
            [[("tt_id", "=", clean_data(record["iCrossVerifierId"]))]],
        )

        print("----->", employee_id)
        print("----approver_id->", approver_id)

        status = False
        if record["iStatusMasterId"] == 54:
            status = "pending"
        if record["iStatusMasterId"] == 55:
            status = "initiated"
        if record["iStatusMasterId"] == 56:
            status = "backout"
        if record["iStatusMasterId"] == 57:
            status = "cancelled"
        if record["iStatusMasterId"] == 58:
            status = "completed"
        if record["iStatusMasterId"] == 59:
            status = "rollback"

        vals = {
            "employee_id": clean_data(employee_id[0]),  # Map fields from MySQL to Odoo
            "tt_id": clean_data(record["iUserHandoverId"]),
            "description": clean_data(record["txNotes"]),
            "approver_id": clean_data(approver_id[0]) if approver_id else False,
            "status": status,
        }

        # print("----->", vals)
        # input("Press Enter to continue...")
        # Check if the record already exists in Odoo
        existing_ids = models.execute_kw(
            odoo_db,
            uid,
            odoo_password,
            odoo_model,
            "search",
            [[("tt_id", "=", record["iUserHandoverId"])]],
        )

        if existing_ids:
            # Update existing record
            models.execute_kw(
                odoo_db, uid, odoo_password, odoo_model, "write", [existing_ids, vals]
            )
            print(f"Updated record {record['iUserHandoverId']}")
        else:
            # Create new record
            models.execute_kw(odoo_db, uid, odoo_password, odoo_model, "create", [vals])
            print(f"Created new record {record['iUserHandoverId']}")


def main():
    # Connect to Odoo and MySQL
    models, uid = connect_odoo()
    connection = connect_mysql()

    # Define the table name in MySQL and corresponding model in Odoo
    mysql_table = "user_handover"
    odoo_model = "employee.handover"

    # Fetch data from MySQL
    mysql_data = fetch_mysql_data(connection, mysql_table)

    # Import data into Odoo
    import_data_to_odoo(models, uid, odoo_model, mysql_data)


if __name__ == "__main__":
    main()
