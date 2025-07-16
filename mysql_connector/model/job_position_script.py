import xmlrpc.client
import mysql.connector

# Odoo connection details
odoo_url = "http://127.0.0.67:8069/xmlrpc/2"
odoo_db = "internal_erp_1_july_25"
odoo_username = "admin"
odoo_password = "admin"


# MySQL connection details
mysql_host = "localhost"
mysql_user = "root"
mysql_password = "ur48x"
mysql_db = "tt_db_v1_p"



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
    print("\n\n===============>", result)
    return result


def import_data_to_odoo(models, uid, odoo_model, data):
    """Insert data into Odoo via XML-RPC."""
    for record in data:

        # Search for the designation in Odoo
        department_id = models.execute_kw(
            odoo_db,
            uid,
            odoo_password,
            "hr.department",
            "search",
            [[("tt_id", "=", record.get("iDepartmentMasterId", 0))]],
        )

        vals = {
            "name": record.get("vDesignationName", ""),
            "tt_id": record.get("iDesignationMasterId", 0),
            "department_id": department_id[0] if department_id else False,
            "active": True if record["iStatusMasterId"] == 1 else False,
        }

        # Check if the record already exists in Odoo
        existing_ids = models.execute_kw(
            odoo_db,
            uid,
            odoo_password,
            odoo_model,
            "search",
            [[("tt_id", "=", record["iDesignationMasterId"])]],
        )

        if existing_ids:
            # Update existing record
            models.execute_kw(
                odoo_db, uid, odoo_password, odoo_model, "write", [existing_ids, vals]
            )
            print(f"Updated record {record['vDesignationName']}")
        else:
            # Create new record
            if vals:
                models.execute_kw(
                    odoo_db, uid, odoo_password, odoo_model, "create", [vals]
                )
                print(f"Created new record {record['vDesignationName']}")


def main():
    # Connect to Odoo and MySQL
    models, uid = connect_odoo()
    connection = connect_mysql()

    # Define the table name in MySQL and corresponding model in Odoo
    mysql_table = "designation_master"
    odoo_model = "hr.job"

    # Fetch data from MySQL
    mysql_data = fetch_mysql_data(connection, mysql_table)

    # Import data into Odoo
    import_data_to_odoo(models, uid, odoo_model, mysql_data)


if __name__ == "__main__":
    main()
