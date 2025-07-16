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
    for record in data:
        connection = connect_mysql()
        cursor = connection.cursor(dictionary=True)
        print("cursor--->", cursor)
        def clean_data(value):
            return value if value is not None else ''

        country_id = False

        if record.get("iCountryId"):
            cursor.execute(
                "SELECT vCountry FROM country_master WHERE iCountryId = %s",
                (record["iCountryId"],),
            )
            country = cursor.fetchall()
            print("country--->", country)
            country = country[0]['vCountry']

            if country:
                country_id = models.execute_kw(
                    odoo_db,
                    uid,
                    odoo_password,
                    "res.country",
                    "search",
                    [[["name", "=", country]]],
                )

                print("country_id--->", country_id)

        vals = {
            "tt_id": clean_data(record.get("iClientId")),
            "name": f"{clean_data(record.get('vFirstName'))} {clean_data(record.get('vLastName'))}",
            "email": clean_data(record.get("vEmail")),
            "phone": clean_data(record.get("vContactNumber")),
            "website": clean_data(record.get("vCompanyUrl")),
            "street": clean_data(record.get("txAddress")),
            "mobile": clean_data(record.get("vNumber")),
            "comment": clean_data(record.get("txCompanyDetail")),
            "country_id": country_id[0] if country_id else False,
            # "function": clean_data(record.get("vSignature")),
            "skype": clean_data(record.get("vSkypeId")),
            "slack": clean_data(record.get("vSlackId")),
            "gmail": clean_data(record.get("vGmailId")),
        }

        print("\nDebug---------------------- vals:", vals)

        # Check if the record already exists in Odoo
        existing_ids = models.execute_kw(
            odoo_db,
            uid,
            odoo_password,
            odoo_model,
            "search",
            [[("email", "=", record["vEmail"])]],
        )

        if existing_ids:
            # Update existing record
            models.execute_kw(
                odoo_db, uid, odoo_password, odoo_model, "write", [existing_ids, vals]
            )
            print(f"Updated record {record['vFirstName']} {record['vLastName']}")
        else:
            # Create new record
            if vals:
                models.execute_kw(
                    odoo_db, uid, odoo_password, odoo_model, "create", [vals]
                )
                print(f"Created new record {record['vFirstName']} {record['vLastName']}")


def main():
    # Connect to Odoo and MySQL
    models, uid = connect_odoo()
    connection = connect_mysql()

    # Define the table name in MySQL and corresponding model in Odoo
    mysql_table = "client_master"
    odoo_model = "res.partner"

    # Fetch data from MySQL
    mysql_data = fetch_mysql_data(connection, mysql_table)

    # Import data into Odoo
    import_data_to_odoo(models, uid, odoo_model, mysql_data)


if __name__ == "__main__":
    main()
