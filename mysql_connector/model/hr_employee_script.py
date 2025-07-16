import xmlrpc.client
import mysql.connector
import pprint
from datetime import datetime, date

# Odoo connection details
ODOO_URL = "http://localhost:8069/xmlrpc/2"
ODOO_DB = "internal_erp_1_july_25"
ODOO_USERNAME = "admin"
ODOO_PASSWORD = "admin"

# MySQL connection details
MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "ur48x",
    "database": "tt_db_v1_p",
    # "port": 3306,
}



def connect_odoo():
    """Connect to Odoo via XML-RPC and return models object."""
    try:
        common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/common")
        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})

        if not uid:
            raise Exception("Failed to authenticate with Odoo")

        models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/object")

        print("✅ Connected to Odoo successfully!")
        return models, uid
    except Exception as e:
        raise Exception(f"❌ Odoo Connection Error: {e}")


def connect_mysql():
    """Connect to MySQL and return the connection object."""
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        print("✅ Connected to MySQL successfully!")
        return connection
    except mysql.connector.Error as err:
        raise Exception(f"❌ MySQL Connection Error: {err}")


def fetch_mysql_data(connection, table_name):
    """Fetch unique user data from MySQL based on email."""
    query = f"""
        SELECT *
        FROM {table_name}
        WHERE iUserId IN (
            SELECT MAX(iUserId)
            FROM {table_name}
            GROUP BY vEmailId
        )
    """

    with connection.cursor(dictionary=True) as cursor:
        cursor.execute(query)
        result = cursor.fetchall()

    print(f"🔍 Fetched {len(result)} unique records from MySQL.")
    return result


def format_date(date_value):
    """Convert date to 'YYYY-MM-DD' format, return None if invalid."""
    if isinstance(date_value, (datetime, date)):
        return date_value.strftime("%Y-%m-%d")  # Date only
    return False


def format_datetime(date_value):
    """Convert date to 'YYYY-MM-DD HH:MI:SS' format, return None if invalid."""
    if isinstance(date_value, datetime):  # Ensure it's a datetime object
        return date_value.strftime("%Y-%m-%d %H:%M:%S")  # Full timestamp
    elif isinstance(date_value, date):  # Convert date to datetime
        return datetime(date_value.year, date_value.month, date_value.day).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    return False


def split_address(address):
    """Split an address string and return structured data."""
    parts = [p.strip() for p in address.split(",") if p.strip()]
    return {
        "house_number": parts[0] if len(parts) > 0 else "",
        "street": parts[1] if len(parts) > 1 else "",
        "locality": parts[2] if len(parts) > 2 else "",
        "city": (
            parts[-1].split("-")[0]
            if len(parts) > 3 and "-" in parts[-1]
            else parts[-1] if len(parts) > 3 else ""
        ),
        "pincode": (
            parts[-1].split("-")[1] if len(parts) > 3 and "-" in parts[-1] else ""
        ),
    }


def import_data_to_odoo(models, uid, odoo_model, data):
    """Insert or update data in Odoo via XML-RPC."""
    print(f"\n🔄 Processing {len(data)} records...")

    for record in data:
        # Process addresses
        current_address = split_address(record.get("txCurrentAddress", ""))
        permanent_address = split_address(record.get("txPermanentAddress", ""))

        user_id = models.execute_kw(
            ODOO_DB,
            uid,
            ODOO_PASSWORD,
            "res.users",
            "search",
            [[("tt_id", "=", record.get("iUserId"))]],
        )

        job_id = models.execute_kw(
            ODOO_DB,
            uid,
            ODOO_PASSWORD,
            "hr.job",
            "search",
            [[("tt_id", "=", record.get("iDesignationMasterId"))]],
        )

        department_id = models.execute_kw(
            ODOO_DB,
            uid,
            ODOO_PASSWORD,
            "hr.department",
            "search",
            [[("tt_id", "=", record.get("iDepartmentMasterId"))]],
        )

        # Prepare Odoo data payload
        vals = {
            "name": f"{record.get('vFirstName', '')} {record.get('vLastName', '')}",
            "tt_id": record.get("iUserId"),
            "department_id": department_id[0] if department_id else False,
            # "sub_desination_id": record.get("iSubDesignationMasterId"),
            # "designation_id": record.get("iDesignationMasterId"),
            "job_id": job_id[0] if job_id else False,
            "work_email": record.get("vEmailId"),
            "mobile_phone": record.get("vMobileNumber"),
            "joining_date": format_date(record.get("dtJoiningDate")),
            "birthday": format_date(record.get("dtDob")),
            "gender": {"M": "male", "F": "female"}.get(record.get("eGender"), "other"),
            "marital": {1: "single", 0: "married"}.get(
                record.get("tiMaritalStatus"), "divorced"
            ),
            "svn_user_id": record.get("vSvnUserName"),
            "carrier_start_date": format_datetime(record.get("dtCarrerStartDate")),
            "relieve_date": format_datetime(record.get("dtReleavingDate")) or False,
            "emergency_phone": record.get("vAlternateNumber1"),
            "emergency_contact": record.get("vAlternatePerson1"),
            "emergency_contact_relation": record.get("vAlternateRelation1"),
            "emergency_phone_2": record.get("vAlternateNumber2"),
            "emergency_contact_2": record.get("vAlternatePerson2"),
            "emergency_contact_relation_2": record.get("vAlternateRelation2"),
            "emp_code": record.get("vEmployeeCode"),
            "private_street": current_address["street"],
            "private_street2": current_address["house_number"],
            "private_city": current_address["city"],
            "private_zip": current_address["pincode"],
            "permanent_street": permanent_address["street"],
            "permanent_street2": permanent_address["house_number"],
            "permanent_city": permanent_address["city"],
            "permanent_zip": permanent_address["pincode"],
            "user_id": user_id[0] if user_id else None,
            "active": True if record["iStatusMasterId"] == 1 else False,
            "status": "permanent",
        }

        vals = {k: v for k, v in vals.items() if v is not None}

        print("*******************\n", vals)
        # input("Press Enter to continue...")
        # Check if user already exists in Odoo
        existing_ids = models.execute_kw(
            ODOO_DB,
            uid,
            ODOO_PASSWORD,
            odoo_model,
            "search",
            [[("tt_id", "=", record.get("iUserId"))]],
        )
        print(existing_ids)

        if existing_ids:
            models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD, odoo_model, "write", [existing_ids, vals]
            )
            print(f"✅ Updated Employee ID {record.get('iUserId')}")
        else:
            if record["iStatusMasterId"] == 1:
                models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, odoo_model, "create", [vals])
                print(f"✅ Created New Employee ID {record.get('iUserId')}")
            else:
                print(f"❌ Employee ID {record.get('iUserId')} is inactive")


def main():
    try:
        # Connect to Odoo and MySQL
        models, uid = connect_odoo()
        connection = connect_mysql()

        # Define MySQL table and Odoo model
        mysql_table = "user_master"
        odoo_model = "hr.employee"

        # Fetch data from MySQL
        mysql_data = fetch_mysql_data(connection, mysql_table)

        # Import data into Odoo
        import_data_to_odoo(models, uid, odoo_model, mysql_data)

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
