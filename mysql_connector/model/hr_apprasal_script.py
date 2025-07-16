
from typing import Union
import xmlrpc.client
import mysql.connector
from datetime import datetime, date

# Odoo connection details
odoo_url = "http://localhost:9595/xmlrpc/2"
odoo_db = "hrms_db"
odoo_username = "admin"
odoo_password = "admin"


# MySQL connection details
mysql_host = 'localhost'
mysql_user = 'root'
mysql_password = '12345678'
mysql_db = 'tingtong_v2'



def connect_odoo():
    """Connect to Odoo via XML-RPC and return models object."""
    common = xmlrpc.client.ServerProxy('{}/common'.format(odoo_url))
    uid = common.authenticate(odoo_db, odoo_username, odoo_password, {})

    if uid:
        models = xmlrpc.client.ServerProxy('{}/object'.format(odoo_url))
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
            port=3306
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
    def format_date(date_value: Union[datetime, date]) -> str:  
        """
        Format a datetime or date object into a string with the format 'YYYY-MM-DD HH:MM:SS'.

        Args:
            date_value: The datetime or date object to be formatted.

        Returns:    
            The formatted string.
        """
        if isinstance(date_value, (datetime, date)):
            return date_value.strftime('%Y-%m-%d %H:%M:%S')
        return False
    
    for record in data:
        # Convert comma-separated string to a list of integers
        reporting_managers = record.get('vReportingManagers')
        if isinstance(reporting_managers, str):
            reporting_manager_ids = [int(x) for x in reporting_managers.split(',') if x.isdigit()]
        elif isinstance(reporting_managers, int):
            reporting_manager_ids = [reporting_managers]  # If it's a single integer
        else:
            reporting_manager_ids = []

        # Extract reviewer IDs
        reviewers = record.get('iReviewerId')
        if isinstance(reviewers, str):
            reviewer_ids = [int(x) for x in reviewers.split(',') if x.isdigit()]
        elif isinstance(reviewers, int):
            reviewer_ids = [reviewers]  # If it's a single integer
        else:
            reviewer_ids = []

        # Combine reporting managers and reviewers, removing duplicates
        manager_ids = list(set(reporting_manager_ids + reviewer_ids))

        # Construct domains to search for employee records
        interviewer_ids_domain = [('tt_id', 'in', manager_ids)] if manager_ids else [('tt_id', '=', False)]
        employee_ids_domain = [('tt_id', '=', record.get('iUserId'))] if record.get('iUserId') else [('tt_id', '=', False)]

        print('interviewer_ids_domain:', interviewer_ids_domain)
        print('employee_ids_domain:', employee_ids_domain)

        # Search for employee based on tt_id
        employee_id = models.execute_kw(odoo_db, uid, odoo_password, 'hr.employee', 'search', [employee_ids_domain])

        # Search for interviewers (managers + reviewers) based on tt_id
        user_ids = models.execute_kw(odoo_db, uid, odoo_password, 'hr.employee', 'search_read', [interviewer_ids_domain], {'fields': ['id']})
        print("\n\nUser IDs:", user_ids)

        # Extract IDs of interviewers
        interviewer_user_ids = [emp['id'] for emp in user_ids if emp.get('id')]
        print("Interviewer User IDs:", interviewer_user_ids)

        # Prepare data to send to Odoo
        vals = {
            'employee_id': employee_id[0] if employee_id else False,
            'hr_manager_ids': [(6, 0, interviewer_user_ids)],
            'hr_manager': True if manager_ids else False,
            'tt_id': record.get('iAppraisalId'),
            'appraisal_deadline': format_date(record.get('dtLastApprisalDate')) if record.get('dtLastApprisalDate') else datetime.today().strftime('%Y-%m-%d'),
        }

        # Check if the record already exists in Odoo
        existing_ids = models.execute_kw(odoo_db, uid, odoo_password, odoo_model, 'search', [[('tt_id', '=', record.get('iAppraisalId'))]])

        # Update or create the record based on existence
        if existing_ids:
            models.execute_kw(odoo_db, uid, odoo_password, odoo_model, 'write', [existing_ids, vals])
            print(f"Updated record {record.get('iAppraisalId')}")
        else:
            models.execute_kw(odoo_db, uid, odoo_password, odoo_model, 'create', [vals])
            print(f"Created new record {record.get('iAppraisalId')}")

def main():
    # Connect to Odoo and MySQL
    models, uid = connect_odoo()
    connection = connect_mysql()

    # Define the table name in MySQL and corresponding model in Odoo
    mysql_table = 'appraisal_master'
    odoo_model = 'hr.appraisal'

    # Fetch data from MySQL
    mysql_data = fetch_mysql_data(connection, mysql_table)

    # Import data into Odoo
    import_data_to_odoo(models, uid, odoo_model, mysql_data)

if __name__ == "__main__":
    main()
