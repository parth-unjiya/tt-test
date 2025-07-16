
import xmlrpc.client
import mysql.connector
from datetime import datetime, date

# Odoo connection details
odoo_url = "http://127.0.0.67:6767/xmlrpc/2"
odoo_db = "hrms_db_21_02_25"
odoo_username = "admin"
odoo_password = "admin"


# MySQL connection details
mysql_host = "localhost"
mysql_user = "root"
mysql_password = "Aa@12345678"
mysql_db = "tt_staging_v21"



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
    for record in data:
        interviewer_ids_domain = [('tt_id', '=', record.get('iProjectManagerId'))]
        employee_id = models.execute_kw(odoo_db, uid, odoo_password, 'hr.employee', 'search_read', [interviewer_ids_domain], {'fields': ['user_id']})
        interviewer_user_ids = [emp['user_id'][0] for emp in employee_id if emp.get('user_id')]
        print("--record.get('iProjectManagerId')--->", record.get('iProjectManagerId'))
        print("----->", interviewer_user_ids)
        # 5/0
        # Handle date fields with type checks
        def format_date(date_value):
            if isinstance(date_value, (datetime, date)):
                print("Debug======================date_value----->", date_value)
                return date_value.strftime('%Y-%m-%d')
            return ''  

        # Prepare the data to send to Odoo
        vals = {
            'name': record.get('vProjectName'),
            'tt_id': record.get('iProjectId'),
            'user_id': interviewer_user_ids[0] if interviewer_user_ids else False,
            'date_start': format_date(record.get('dtProjectStart')) if record.get('dtProjectStart') else False,
            'date': format_date(record.get('dtProjectDue')) if record.get('dtProjectDue') else False,

        }

        # Check if the record already exists in Odoo
        existing_ids = models.execute_kw(odoo_db, uid, odoo_password, odoo_model, 'search', [[('tt_id', '=', record.get('iProjectId'))]])

        if existing_ids:
            # Update existing record
            models.execute_kw(odoo_db, uid, odoo_password, odoo_model, 'write', [existing_ids, vals])
            print(f"Updated record {record.get('iProjectId')}")
        else:
            # Create new record
            models.execute_kw(odoo_db, uid, odoo_password, odoo_model, 'create', [vals])
            print(f"Created new record {record.get('iProjectId')}")
            
def main():
    # Connect to Odoo and MySQL
    models, uid = connect_odoo()
    connection = connect_mysql()

    # Define the table name in MySQL and corresponding model in Odoo
    mysql_table = 'project_master'
    odoo_model = 'project.project'

    # Fetch data from MySQL
    mysql_data = fetch_mysql_data(connection, mysql_table)

    # Import data into Odoo
    import_data_to_odoo(models, uid, odoo_model, mysql_data)

if __name__ == "__main__":
    main()
