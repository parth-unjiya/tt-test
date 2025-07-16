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
mysql_password = "Aa@12345678"
mysql_db = "tt_db_v1_p"

def connect_odoo():
    common = xmlrpc.client.ServerProxy(f"{odoo_url}/common")
    uid = common.authenticate(odoo_db, odoo_username, odoo_password, {})
    if uid:
        models = xmlrpc.client.ServerProxy(f"{odoo_url}/object")
        print("✅ Connected to Odoo")
        return models, uid
    raise Exception("❌ Failed to authenticate with Odoo")

def connect_mysql():
    try:
        connection = mysql.connector.connect(
            host=mysql_host,
            user=mysql_user,
            password=mysql_password,
            database=mysql_db,
            port=3306,
        )
        print("✅ Connected to MySQL")
        return connection
    except mysql.connector.Error as err:
        raise Exception(f"❌ MySQL connection error: {err}")

def fetch_mysql_data(connection, table_name):
    cursor = connection.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM {table_name}")
    result = cursor.fetchall()
    cursor.close()
    return result

def import_data_to_odoo(models, uid, odoo_model, data):
    for record in data:
        # Check if already imported by iCandidateReviewId → mapped to `token` field for tracking
        exists = models.execute_kw(
            odoo_db,
            uid,
            odoo_password,
            odoo_model,
            "search",
            [[("token", "=", str(record["iCandidateReviewId"]))]],
        )

        if exists:
            print(f"⏭️ Review {record['iCandidateReviewId']} already exists, skipping.")
            continue

        # Find matching applicant by tt_id
        applicant_ids = models.execute_kw(
            odoo_db,
            uid,
            odoo_password,
            "hr.applicant",
            "search",
            [[("tt_id", "=", record["iCandidateId"])]],
        )

        if not applicant_ids:
            print(f"⚠️ Applicant {record['iCandidateId']} not found.")
            continue

        evaluation_data = {
            "applicant_id": applicant_ids[0],
            "understanding_position": record["iUnderstandingPosition"],
            "technical_skill": record["iSkillSet"],
            "logical_skill": record["iLogicalThinking"],
            "communication_skill": record["iCommunication"],
            "organizational_fit": record["iOrganisationFit"],
            "attitude": record["iAttitude"],
            "work_culture_fit": record["iWorkCultureFit"],
            "new_learning": record["iNewLearning"],
            "tech_1": record["vTechOne"],
            "tech_1_rating": record["iRateTechOne"],
            "tech_2": record["vTechTwo"],
            "tech_2_rating": record["iRateTechTwo"],
            "tech_3": record["vTechThree"],
            "tech_3_rating": record["iRateTechThree"],
            "recommendation": record["eReviewFormType"],  # You may want to map this if enum differs
            "token": str(record["iCandidateReviewId"]),   # Use as external ID for deduplication
            "good_points": record["txGoodComments"],
            "improvement_points": record["txComments"],
            "task_duration": record["vTaskDuration"],
            "task_actual_duration": record["vTaskCompletionDuration"],
            "task_achievement": record["vTaskAchievement"],
            "quality_of_work": record["iQualityOfWork"],
            "recommendation_pr": record["txTaskComments"],
            "good_points_pr": record["vTask"],
            "improvement_points_pr": record["txAdditionalCommentsByTt"],
            "is_not_prectical": False,
            "practical_completed": True,
            "is_filled": True,
        }

        record_id = models.execute_kw(
            odoo_db,
            uid,
            odoo_password,
            odoo_model,
            "create",
            [evaluation_data],
        )
        print(f"✅ Created evaluation: {record_id}")

def main():
    models, uid = connect_odoo()
    connection = connect_mysql()
    mysql_table = "candidate_review"
    odoo_model = "candidate.evaluation"
    mysql_data = fetch_mysql_data(connection, mysql_table)
    import_data_to_odoo(models, uid, odoo_model, mysql_data)

if __name__ == "__main__":
    main()
