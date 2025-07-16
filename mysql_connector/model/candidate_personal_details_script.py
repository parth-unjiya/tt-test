import xmlrpc.client
import mysql.connector
from datetime import datetime, date

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
    try:
        common = xmlrpc.client.ServerProxy(f"{odoo_url}/common")
        uid = common.authenticate(odoo_db, odoo_username, odoo_password, {})

        if not uid:
            raise Exception("Failed to authenticate with Odoo")

        models = xmlrpc.client.ServerProxy(f"{odoo_url}/object")
        print("✅ Connected to Odoo successfully!")
        return models, uid

    except Exception as e:
        print(f"❌ Odoo Connection Error: {e}")
        exit(1)


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
        print("✅ Connected to MySQL successfully!")
        return connection
    except mysql.connector.Error as err:
        print(f"❌ MySQL Connection Error: {err}")
        exit(1)


def fetch_mysql_data(connection, table_name):
    """Fetch data from a specific MySQL table."""
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM {table_name}")
        result = cursor.fetchall()
        cursor.close()
        print(f"🔹 Fetched {len(result)} records from MySQL.")
        return result
    except mysql.connector.Error as err:
        print(f"❌ MySQL Fetch Error: {err}")
        return []


def format_date(date_value):
    """Format date fields safely."""
    if isinstance(date_value, (datetime, date)):
        return date_value.strftime("%Y-%m-%d")
    return False  # Return False for invalid dates


def process_address(address):
    """Split address into parts and handle missing values."""
    parts = address.split(",") if address else []
    return [parts[i] if i < len(parts) else "" for i in range(6)]


def import_data_to_odoo(models, uid, odoo_model, data):
    """Insert or update data in Odoo via XML-RPC."""
    for record in data:
        # Process addresses
        current_address = process_address(record.get("txCurrentAddress", ""))
        permanent_address = process_address(record.get("txPermanentAddress", ""))

        # Check if candidate already exists in Odoo
        employee_id = models.execute_kw(
            odoo_db,
            uid,
            odoo_password,
            odoo_model,
            "search",
            [[("tt_id", "=", record["iCandidateId"])]],
        )

        if not employee_id:
            print(f"❌ Candidate {record['iCandidateId']} not found in Odoo.")
            continue

        personal_data = {
            "dob": format_date(record.get("dBirthDate")),
            "marital": "single" if record.get("tiMaritalStatus") == 1 else "married" if record.get("tiMaritalStatus") == 0 else "divorced",
            "current_street": current_address[0],
            "current_street2": current_address[1],
            "current_city": current_address[2],
            "current_state_id": current_address[4],
            "current_zip": current_address[3],
            "current_country_id": current_address[5],
            "permanent_street": permanent_address[0],
            "permanent_street2": permanent_address[1],
            "permanent_city": permanent_address[2],
            "permanent_state_id": permanent_address[4],
            "permanent_zip": permanent_address[3],
            "permanent_country_id": permanent_address[5],
        }

        # Update record in Odoo
        try:
            result = models.execute_kw(
                odoo_db, uid, odoo_password, odoo_model, "write", [[employee_id[0]], personal_data]
            )
            if result:
                print(f"✅ Updated Candidate {record['iCandidateId']} in Odoo.")
            else:
                print(f"❌ Failed to update Candidate {record['iCandidateId']} in Odoo.")

        except Exception as e:
            print(f"❌ Error updating Candidate {record['iCandidateId']}: {e}")


def main():
    # Connect to Odoo and MySQL
    models, uid = connect_odoo()
    connection = connect_mysql()

    # Define table and model
    mysql_table = "candidate_personal_details"
    odoo_model = "hr.applicant"

    # Fetch and import data
    mysql_data = fetch_mysql_data(connection, mysql_table)
    if mysql_data:
        import_data_to_odoo(models, uid, odoo_model, mysql_data)
    else:
        print("❌ No data found to import.")

    # Close MySQL connection
    connection.close()


if __name__ == "__main__":
    main()
