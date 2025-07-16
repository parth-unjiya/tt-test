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
mysql_password = "Aa@12345678"
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
    # print("===============>", result)
    return result


def import_data_to_odoo(models, uid, odoo_model, data):
    """Insert data into Odoo via XML-RPC."""

    # Helper function to replace None with an empty string
    def clean_data(value):

        return value if value is not None else ""

    for record in data:
        try:

            def format_date(date_value):
                if isinstance(date_value, (datetime, date)):
                    return date_value.strftime("%Y-%m-%d")  # Format the date properly
                return None  # Use None if the date is invalid or None

            # Extract and format the start and end dates
            dCallingTime = format_date(record.get("dCallingTime"))  # '2022-04-12'
            status = False
            if record["iStatusMasterId"] == 35:
                status = "not_interested"
            if record["iStatusMasterId"] == 36:
                status = "ringing"
            if record["iStatusMasterId"] == 37:
                status = "followup"
            if record["iStatusMasterId"] == 38:
                status = "send_mail"
            if record["iStatusMasterId"] == 39:
                status = "future"
            if record["iStatusMasterId"] == 40:
                status = "line_up"

            source_id = False

            if record["iRecruitmentSource"] == 0:
                source_id = 10
            if record["iRecruitmentSource"] == 1:
                source_id = 11
            if record["iRecruitmentSource"] == 2:
                source_id = 12
            if record["iRecruitmentSource"] == 3:
                source_id = 13
            if record["iRecruitmentSource"] == 4:
                source_id = 14
            if record["iRecruitmentSource"] == 5:
                source_id = 15

            reference_id = False

            if record["iEmpRefId"]:
                reference_id = models.execute_kw(
                    odoo_db,
                    uid,
                    odoo_password,
                    "hr.employee",
                    "search",
                    [[("tt_id", "=", clean_data(record["iEmpRefId"]))]],
                )
            # print("reference_id====================", reference_id)
            vals = {
                "name": clean_data(record["vName"]),  # Map fields from MySQL to Odoo
                "tt_id": clean_data(record["iCandidateCallId"]),
                "email": clean_data(record["vEmail"]),
                "consultancy_name": clean_data(record["vConsultancyName"]),
                "source_id": source_id,
                "applied_post": (
                    clean_data(record["vApplyingPost"]) if record["vApplyingPost"] else ""
                ),
                "calling_time": dCallingTime,
                "comments": clean_data(record["txHRComments"]),
                "relevant_experience": clean_data(record["vRelevantExperience"]),
                "career_start_year": clean_data(record["yCarrierStarting"]),
                "mobile": clean_data(record["vMobile"]),
                "company": clean_data(record["vCompanyName"]),
                "reason_for_change": clean_data(record["vReasonForChange"]),
                "social_network": clean_data(record["vSocialNetwork"]),
                "google_sheet": clean_data(record["vGoogleSheetId"]),
                "location": clean_data(record["vLocation"]),
                "current_ctc": clean_data(record["vCurrentCTC"]),
                "expected_ctc": clean_data(record["vExpectedCTC"]),
                "notice_period": clean_data(record["vNoticePeriod"]),
                "linkedin": clean_data(record["vLinkedinLink"]),
                "status": status if status else "future",
                "referral_emp_id": reference_id[0] if reference_id else False,
            }
            # print("\nDebud=================================vals\n", vals)
            # Check if the record already exists in Odoo
            existing_ids = models.execute_kw(
                odoo_db,
                uid,
                odoo_password,
                odoo_model,
                "search",
                [[("tt_id", "=", clean_data(record["iCandidateCallId"]))]],
            )
            # print("Existing====================", existing_ids)

            if not existing_ids:
                # Create new record only if no existing record is found
                models.execute_kw(odoo_db, uid, odoo_password, odoo_model, 'create', [vals])
                print(f"Created new record {clean_data(record['vName'])}")
            else:
                models.execute_kw(
                    odoo_db, uid, odoo_password, odoo_model, "write", [existing_ids, vals]
                )
                # print(f"Updated record {record.get('vName')}")

        except Exception as e:
            print(f"Error processing record {record.get('vName')}: {str(e)}")


def main():
    # Connect to Odoo and MySQL
    models, uid = connect_odoo()
    connection = connect_mysql()
    # Define the table name in MySQL and corresponding model in Odoo
    mysql_table = "candidate_call_master"
    odoo_model = "hr.applicant.call"
    # Fetch data from MySQL
    mysql_data = fetch_mysql_data(connection, mysql_table)
    # Import data into Odoo
    import_data_to_odoo(models, uid, odoo_model, mysql_data)


if __name__ == "__main__":
    main()
