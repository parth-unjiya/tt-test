import xmlrpc.client
import mysql.connector
from datetime import datetime, date
from typing import Union, List

# Odoo connection details
odoo_url = "http://localhost:8069/xmlrpc/2"
odoo_db = "internal_erp_24_feb_25"
odoo_username = "admin"
odoo_password = "admin"

# MySQL connection details
mysql_host = "localhost"
mysql_user = "root"
mysql_password = "ur48x"
mysql_db = "tingtong_v2"


def connect_odoo():
    """Connect to Odoo via XML-RPC and return models object."""
    try:
        common = xmlrpc.client.ServerProxy(f"{odoo_url}/common")
        uid = common.authenticate(odoo_db, odoo_username, odoo_password, {})

        if not uid:
            raise Exception("❌ Failed to authenticate with Odoo.")

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


def fetch_mysql_data(connection, table_name: str) -> List[dict]:
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


def format_date(date_value: Union[datetime, date, None]) -> str:
    """Format a datetime or date object into 'YYYY-MM-DD'."""
    return date_value.strftime("%Y-%m-%d") if isinstance(date_value, (datetime, date)) else False


def get_reviewer_users(models, uid, reviewer_ids: List[int]) -> List[int]:
    """Retrieve user IDs for reviewers from Odoo."""
    if not reviewer_ids:
        return []

    reviewer_domain = ["|"] * (len(reviewer_ids) - 1) + [("tt_id", "=", rid) for rid in reviewer_ids]
    print(f"🔍 Reviewer search domain: {reviewer_domain}")

    user_records = models.execute_kw(
        odoo_db, uid, odoo_password, "hr.employee", "search_read",
        [reviewer_domain], {"fields": ["user_id"]}
    )

    user_ids = [record["user_id"][0] for record in user_records if record.get("user_id")]
    print(f"✅ Retrieved reviewer user IDs: {user_ids}")

    return user_ids


def import_data_to_odoo(models, uid, odoo_model, data):
    """Insert or update probation review data in Odoo."""
    for record in data:
        # Check if employee exists
        employee_ids = models.execute_kw(
            odoo_db, uid, odoo_password, "hr.employee", "search",
            [[("tt_id", "=", record["iUserId"])]]
        )

        if not employee_ids:
            print(f"❌ Employee {record['iUserId']} not found in Odoo.")
            continue

        # Prepare reviewer list
        reviewer_ids = [
            record[key] for key in [
                "iFirstMonthReviewerId",
                "iSecondMonthReviewerId",
                "iThirdMonthReviewerId",
                "iFinalMonthReviewerId",
            ] if record.get(key)
        ]

        reviewer_user_ids = get_reviewer_users(models, uid, reviewer_ids)

        # Determine review type
        review_type = str(record["tiReviewerType"]) if record["tiReviewerType"] in [1, 2, 3, 4] else "0"

        probation_data = {
            "tt_id": record["iProbationPeriodId"],
            "employee_id": employee_ids[0],
            "review_type": review_type,
            "reviewer_ids": [(6, 0, reviewer_user_ids)] if reviewer_user_ids else False,
            "start_date": format_date(record.get("dDueProbationReviewDate")),
            "end_date": format_date(record.get("dFinalProbationReviewDate")),
        }
        input("Press Enter to continue...")
        # Write probation review data to Odoo
        try:
            result = models.execute_kw(
                odoo_db, uid, odoo_password, "hr.employee", "write",
                [employee_ids, {"review_ids": [(0, 0, probation_data)]}]
            )

            if result:
                print(f"✅ Probation review added for Employee {record['iUserId']}.")
            else:
                print(f"❌ Failed to add probation review for Employee {record['iUserId']}.")
        except Exception as e:
            print(f"❌ Error updating Employee {record['iUserId']}: {e}")


def main():
    # Connect to Odoo and MySQL
    models, uid = connect_odoo()
    connection = connect_mysql()

    # Define table and model
    mysql_table = "probation_period_master"
    odoo_model = "hr.employee.probation.review"

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
