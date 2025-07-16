import xmlrpc.client
import mysql.connector
import json

# Odoo connection details
odoo_url = "https://tingtong.spaceo.in/xmlrpc/2"
odoo_db = "tingtong_v1"
odoo_username = "admin@admin.com"
odoo_password = "ur48x"


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

    # columns = ["iUserId", "vEmailId", "vFirstName"]

    # column_str = ", ".join(columns)

    # All user Take
    # query = f"""
    #         SELECT iUserId, vEmailId, vFirstName, vLastName, iStatusMasterId
    #         FROM {table_name}
    #         WHERE iUserId IN (
    #             SELECT MAX(iUserId) 
    #             FROM {table_name} 
    #             GROUP BY vEmailId
    #         )
    #     """
    # only active user
    query = f"""
        SELECT iUserId, vEmailId, vFirstName, vLastName, iStatusMasterId
        FROM {table_name}
        WHERE iStatusMasterId = 1
          AND iUserId IN (
            SELECT MAX(iUserId)
            FROM {table_name}
            WHERE iStatusMasterId = 1
            GROUP BY vEmailId
        )
    """

    # cursor.execute(f"SELECT {column_str} FROM {table_name}")
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    # print("===============>", result)
    print("===============>", len(result))
    return result


def import_data_to_odoo(models, uid, odoo_model, data):
    """Insert data into Odoo via XML-RPC."""

    print("\n\nDEBUG: ========Total Records: =======", len(data))
    for record in data:
        tt_id = record.get("iUserId", "")
        vEmailId = record.get("vEmailId", "")
        vFirstName = record.get("vFirstName", "")
        vLastName = record.get("vLastName", "")

        vals = {
            "tt_id": tt_id,
            # "login": vEmailId,
            "name": f"{vFirstName.strip()} {vLastName.strip()}".strip(),
            # "active": True if record["iStatusMasterId"] == 1 else False,
        }

        print(vals)
        
        # Check if the record already exists in Odoo
        existing_ids = models.execute_kw(
            odoo_db,
            uid,
            odoo_password,
            odoo_model,
            "search",
            [[("tt_id", "=", record["iUserId"])]],
        )

        if existing_ids:
            # Update existing record
            models.execute_kw(
                odoo_db, uid, odoo_password, odoo_model, "write", [existing_ids, vals]
            )
            print(f"Updated record {record['vFirstName']}")
        # else:
        #     if record["iStatusMasterId"] == 1:
        #         # Create new record
        #         models.execute_kw(odoo_db, uid, odoo_password, odoo_model, "create", [vals])
        #         print(f"Created new record {record['vFirstName']}")
        #     else:
        #         print(f"Skipped record {record['vFirstName']}")


def main():
    # Connect to Odoo and MySQL
    models, uid = connect_odoo()
    connection = connect_mysql()

    # Define the table name in MySQL and corresponding model in Odoo
    mysql_table = "user_master"
    odoo_model = "res.users"

    # Fetch data from MySQL
    mysql_data = fetch_mysql_data(connection, mysql_table)

    # Import data into Odoo
    import_data_to_odoo(models, uid, odoo_model, mysql_data)


if __name__ == "__main__":
    main()
