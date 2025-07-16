import mysql.connector
import psycopg2
from datetime import datetime

# ---------- MySQL Configuration ----------

mysql_config = {
    "host": "localhost",
    "user": "root",
    "password": "ur48x",
    "database": "tt_db_v1_p",
}

# ---------- PostgreSQL Configuration ----------

postgres_config = {
    "dbname": "tingtong_v1",
    "user": "postgres",  # Adjust if needed
    "password": "6wzaF8wM3Vwz2",  # 🔒 Replace this
    "host": "15.207.148.83",
    "port": "5432",
    # 15.207.148.83
}

# ---------- Connect to PostgreSQL and Update create_date ----------

def update_create_date_pgsql(record_id, create_date_str):
    try:
        conn = psycopg2.connect(**postgres_config)
        cursor = conn.cursor()
        query = """
            UPDATE hr_applicant_call
            SET create_date = %s
            WHERE id = %s
        """
        cursor.execute(query, (create_date_str, record_id))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"🗓️ Updated Odoo ID {record_id} → {create_date_str}")
    except Exception as e:
        print(f"❌ PostgreSQL error: {e}")

# ---------- Main Script ----------

def update_create_dates():
    try:
        # Connect MySQL
        mysql_conn = mysql.connector.connect(**mysql_config)
        mysql_cursor = mysql_conn.cursor(dictionary=True)

        # Connect PostgreSQL
        pg_conn = psycopg2.connect(**postgres_config)
        pg_cursor = pg_conn.cursor()

        # Get MySQL data
        mysql_cursor.execute("SELECT iCandidateCallId, iCreatedAt FROM candidate_call_master WHERE iCreatedAt IS NOT NULL LIMIT 20")
        rows = mysql_cursor.fetchall()

        for row in rows:
            tt_id = row['iCandidateCallId']
            timestamp = row['iCreatedAt']
            
            if not timestamp:
                continue

            # Convert Unix timestamp to datetime
            try:
                create_date = datetime.fromtimestamp(int(timestamp))
            except Exception as e:
                print(f"⚠️ Skipping TT ID {tt_id} due to invalid timestamp: {timestamp}")
                continue

            # Find Odoo record ID using tt_id
            pg_cursor.execute("SELECT id FROM hr_applicant_call WHERE tt_id = %s", (str(tt_id),))
            result = pg_cursor.fetchone()

            if result:
                odoo_id = result[0]
                update_create_date_pgsql(odoo_id, create_date.strftime("%Y-%m-%d %H:%M:%S"))
            else:
                print(f"❌ No Odoo record found for TT ID {tt_id}")

        mysql_cursor.close()
        mysql_conn.close()
        pg_cursor.close()
        pg_conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    update_create_dates()
