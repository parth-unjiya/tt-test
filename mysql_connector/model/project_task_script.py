
import xmlrpc.client
import mysql.connector
from datetime import datetime, date

# Odoo connection details
odoo_url = "http://127.0.0.67:8069/xmlrpc/2"
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
    # print("===============>", result)
    return result



def import_data_to_odoo(models, uid, odoo_model, data):
    """Insert or update records in Odoo using XML-RPC."""

    for record in data:
        user_tt_id = record.get('iUserId')
        project_task_id = record.get('iProjectTaskId')
        project_id = record.get('iProjectId')
        task_name = record.get('vTask')
        estimated_time = record.get('iEstimatedTime')

        if not all([project_id]):
            print(f"⚠️ Skipping record due to missing required fields: {record}")
            continue

        # Fetch user directly from res.users using tt_id
        user_domain = [('tt_id', '=', user_tt_id)]
        users = models.execute_kw(
            odoo_db, uid, odoo_password,
            'res.users', 'search_read',
            [user_domain], {'fields': ['id']}
        )

        user_ids = [user['id'] for user in users]

        
        project = models.execute_kw(
            odoo_db, uid, odoo_password,   
            'project.project', 'search',
            [[('tt_id', '=', project_id)]]
        )

        # Prepare values for creation/updating
        vals = {
            'name': task_name,
            'tt_id': project_task_id,
            'project_id': project[0],
            'user_ids': [(6, 0, user_ids)] if user_ids else False,
            'allocated_hours': estimated_time,
        }

        # Check if record already exists
        existing_ids = models.execute_kw(
            odoo_db, uid, odoo_password,
            odoo_model, 'search',
            [[('tt_id', '=', project_task_id)]]
        )

        if existing_ids:
            models.execute_kw(
                odoo_db, uid, odoo_password,
                odoo_model, 'write',
                [existing_ids, vals]
            )
            print(f"✔️ Updated task with tt_id={project_task_id}")
        else:
            models.execute_kw(
                odoo_db, uid, odoo_password,
                odoo_model, 'create',
                [vals]
            )
            print(f"➕ Created new task with tt_id={project_task_id}")




            
def main():
    # Connect to Odoo and MySQL
    models, uid = connect_odoo()
    connection = connect_mysql()

    # Define the table name in MySQL and corresponding model in Odoo
    mysql_table = 'project_tasks'
    odoo_model = 'project.task'

    # Fetch data from MySQL
    mysql_data = fetch_mysql_data(connection, mysql_table)

    # Import data into Odoo
    import_data_to_odoo(models, uid, odoo_model, mysql_data)

if __name__ == "__main__":
    main()
