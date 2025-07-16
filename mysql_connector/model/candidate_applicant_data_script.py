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

    def clean_numeric(value):
        try:
            return float(value)  # Convert to float
        except (ValueError, TypeError):
            return 0.0

    for record in data:

        def format_date(date_value):
            if isinstance(date_value, (datetime, date)):
                return date_value.strftime("%Y-%m-%d")  # Format the date properly
            return False  # Use None if the date is invalid or None

        # Extract and format the interview date
        interview_date = format_date(record.get("dtInterviewDate"))
        
        # Create a list of interviewer IDs, filtering out None values
        interviewer_ids = [
            record.get("iSecondInterviewer"),
            record.get("iFirstInterviewer"),
            record.get("iPracticalReviewer"),
        ]
        # # Remove None values from interviewer_ids
        # interviewer_ids = [id_ for id_ in interviewer_ids if id_ is not None]

        # # Create a domain to match any interviewer based on 'tt_id'
        # interviewer_ids_domain = []
        # if interviewer_ids:
        #     # Start building the domain
        #     interviewer_ids_domain = ["|"] * (len(interviewer_ids) - 1) + [
        #         ("tt_id", "=", id_) for id_ in interviewer_ids
        #     ]


        # Remove None values from interviewer_ids
        interviewer_ids = [id_ for id_ in interviewer_ids if id_ not in (None, 0)]

        print("===>interviewer_ids", interviewer_ids)

        # Create a domain to match any interviewer based on 'tt_id'
        if interviewer_ids:
            interviewer_ids_domain = ["|"] * (len(interviewer_ids) - 1) + [
                ("tt_id", "=", id_) for id_ in interviewer_ids
            ]
        else:
            interviewer_ids_domain = []

        print("===>interviewer_ids_domain", interviewer_ids_domain)

        # input("Press Enter to continue...")

        # Fetch employee records, including user_id, and filter out None values for user_id
        print("===>Email selected", record.get("txEmailSelected"))
        tx_email_selected = record.get(
            "txEmailSelected", ""
        )  # Get the value or default to an empty string

        if tx_email_selected is None:
            continue

        # Split the string into a list of IDs and convert them to integers
        id_list = [
            int(id.strip())
            for id in tx_email_selected.split(",")
            if id.strip().isdigit()
        ]

        # Define the domain to search for multiple tt_id values
        user_email_domain = [
            ("tt_id", "in", id_list)
        ]  # Use 'in' to match any of the IDs in the list
        print("===>user_email_domain", user_email_domain)
        # Fetch user emails based on the defined domain
        user_email = models.execute_kw(
            odoo_db,
            uid,
            odoo_password,
            "hr.employee",
            "search_read",
            [user_email_domain],
            {"fields": ["work_email"]},
        )
        print("===>user_email", user_email)
        # Extract user_ids from the result
        user_email1 = [
            emp_email["work_email"]
            for emp_email in user_email
            if emp_email.get("work_email")
        ]
        print("===>user_email1", user_email1)
        string_user_email = ",".join(str(i) for i in user_email1)
        
        if interviewer_ids_domain:
            employee_ids = models.execute_kw(
                odoo_db,
                uid,
                odoo_password,
                "hr.employee",
                "search_read",
                [interviewer_ids_domain],
                {"fields": ["user_id"]},
            )
        else:
            employee_ids = []

        # user_email = models.execute_kw(odoo_db, uid, odoo_password, 'hr.employee', 'search_read', [user_email_domain], {'fields': ['user_id']})

        # Filter out employees with None in user_id
        interviewer_user_ids = [
            emp["user_id"][0] for emp in employee_ids if emp.get("user_id")
        ]

        # print("======>", clean_data(record["vApplyingPost"]))
        # input("Press Enter to continue...")
        
        # job_id = models.execute_kw(
        #     odoo_db,   
        #     uid,
        #     odoo_password,
        #     "hr.job",
        #     "search",
        #     [[("name", "=", clean_data(record["vApplyingPost"]))]]
        # )
        # print("===>job_id", job_id)
        # # input("Press Enter to continue...")
        # if not job_id:
        #     job = models.execute_kw(
        #         odoo_db, 
        #         uid, 
        #         odoo_password, 
        #         "hr.job", 
        #         "create", 
        #         [{"name": clean_data(record["vApplyingPost"])}]
        #     )
        #     print(f"Created new Job { record['vApplyingPost'] } with ID: {job_id}")

        status = False
        if record["iStatusMasterId"] == 7:
            status = 'Candidate Process'
        if record["iStatusMasterId"] == 8:
            status = 'Hold'
        if record["iStatusMasterId"] == 9:
            status = 'Review Process'
        if record["iStatusMasterId"] == 10:
            status = 'Contract Signed'
        if record["iStatusMasterId"] == 11:
            status = 'Rejected'
        if record["iStatusMasterId"] == 13:
            status = 'Not Appeared'
        if record["iStatusMasterId"] == 14:
            status = 'Backout'

        stage_id = False
        if status:
            stage_ids = models.execute_kw(
                odoo_db,
                uid,
                odoo_password,
                'hr.recruitment.stage',
                'search',
                [[('name', '=', status)]]
            )

            if stage_ids:
                stage_id = stage_ids[0]
            else:
                stage_id = models.execute_kw(
                    odoo_db,
                    uid,
                    odoo_password,
                    'hr.recruitment.stage',
                    'create',
                    [{'name': status}]
                )
                print(f"🆕 Created new recruitment stage: {status} (ID: {stage_id})")


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


        # print("\n+++++++++++++++++++ Job id", job_id, "\n\n")
        # Create a new record
        vals = {
            "name": clean_data(record["vName"]),
            "partner_name": clean_data(record["vName"]),
            "tt_id": clean_data(record["iCandidateId"]),
            "email_from": clean_data(record["vEmail"]),
            "consultancy_name": clean_data(record["vConsultancyName"]),
            "source_id": source_id,
            "applied_post": (
                clean_data(record["vApplyingPost"]) if record["vApplyingPost"] else ""
            ),
            # "referral_emp_id": clean_data(record["iEmpRefId"]) or False,
            "description": clean_data(record["txHRComments"]) or False,
            "relevant_experience": clean_data(record["vRelevantExperience"]) or False,
            "partner_mobile": clean_data(record["vMobile"]),
            "company": clean_data(record["vCompanyName"]),
            "reason_for_change": clean_data(record["vReasonForChange"]),
            "social_network": clean_data(record["vSocialNetwork"]),
            "google_sheet": clean_data(record["vGoogleSheetId"]),
            "location": clean_data(record["vLocation"]),
            "salary_current": clean_numeric(record["vCurrentCTC"]) or False,
            "salary_expected": clean_numeric(record["vExpectedCTC"]),
            "notice_period": clean_data(record["vNoticePeriod"]),
            "linkedin_profile": clean_data(record["vLinkedinLink"]),
            "email_cc": string_user_email if string_user_email else "",
            "interviewer_ids": [
                (6, 0, interviewer_user_ids)
            ],
            "referral_emp_id": reference_id[0] if reference_id else False,
            "stage_id": stage_id,
        }


        print("===>vals", vals)
        # input("Press Enter to continue...")

        # Check if the record already exists in Odoo
        existing_ids = models.execute_kw(
            odoo_db,
            uid,
            odoo_password,
            odoo_model,
            "search",
            [[("tt_id", "=", record.get("iCandidateId"))]],
        )

        if existing_ids:
            # Update existing record
            models.execute_kw(
                odoo_db, uid, odoo_password, odoo_model, "write", [existing_ids, vals]
            )
            print(f"Updated record {record.get('iCandidateId')}")
        else:
            # Create new record
            models.execute_kw(odoo_db, uid, odoo_password, odoo_model, "create", [vals])
            print(f"Created new record {record.get('iCandidateId')}")


def main():
    # Connect to Odoo and MySQL
    models, uid = connect_odoo()
    connection = connect_mysql()

    # Define the table name in MySQL and corresponding model in Odoo
    mysql_table = "candidate_master"
    odoo_model = "hr.applicant"

    # Fetch data from MySQL
    mysql_data = fetch_mysql_data(connection, mysql_table)

    # Import data into Odoo
    import_data_to_odoo(models, uid, odoo_model, mysql_data)


if __name__ == "__main__":
    main()
