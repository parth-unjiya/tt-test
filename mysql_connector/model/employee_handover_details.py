
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
    # print("----->", data)
    for record in data:
        # employee_id = models.execute_kw(odoo_db, uid, odoo_password, odoo_model, 'search', [[('tt_id', '=', record['iUserId'])]])
        # vals = {
        #     'tt_id': record.get('iUserId'),
        #     'department_id': record.get('iDepartmentMasterId'),
        #     'sub_desination_id': record.get('iSubDesignationMasterId'),
        #     'designation_id': record.get('iDesignationMasterId'),
          
        # }
        # print(vals)

        # Check if the record already exists in Odoo
        def clean_data(value):
            return value if value is not None else ''
        employee_id_user_handover = models.execute_kw(odoo_db, uid, odoo_password, 'employee.handover', 'search', [[('tt_id', '=', record['iUserHandoverId'])],])
        print("---employee_id_user_handover-->", employee_id_user_handover)
        # record=models.execute_kw(odoo_db, uid, odoo_password, 'hr.employee', 'read', [employee_id], {'fields': ['promotion_history_ids']})
        interviewer_ids_domain = [('tt_id', '=', record.get('iUserId'))]
        print("----->", interviewer_ids_domain)
        employee_id = models.execute_kw(odoo_db, uid, odoo_password, 'hr.employee', 'search_read', [interviewer_ids_domain], {'fields': ['user_id']})
        print("Debug===============================employee_id------>", employee_id)
        interviewer_user_ids = [emp['user_id'][0] for emp in employee_id if emp.get('user_id')]

        task_id = False
        task_name = clean_data(record['vRole'])
        if record['iHandoverTaskId']:
            task_id = models.execute_kw(odoo_db, uid, odoo_password, 'project.task', 'search', [[('tt_id', '=', record['iHandoverTaskId'])]])
            employee_id_user_handover_object = models.execute_kw(odoo_db, uid, odoo_password, 'employee.handover', 'search_read', [[('tt_id', '=', record['iUserHandoverId'])]], {'fields': ['employee_id']})
            task_id_object = models.execute_kw(odoo_db, uid, odoo_password, 'project.task', 'search_read', [[('tt_id', '=', record['iHandoverTaskId'])]], {'fields': ['name']})
            print("Debug===============================employee_id_user_handover_object------>", employee_id_user_handover_object[0].get('employee_id')[1])
            print("Debug===============================task_id_object------>", task_id_object[0].get('name'))
            print("Debug===============================task_id------->", task_id)
            if task_id:
                task_name = task_id_object[0].get('name') + " of " + employee_id_user_handover_object[0].get('employee_id')[1]

        project_id = False
        if record['iProjectId']:
            project_id = models.execute_kw(odoo_db, uid, odoo_password, 'project.project', 'search', [[('tt_id', '=', record['iProjectId'])]])
            print("Debug===============================project_id------->", project_id)

        if employee_id:
            vals = {
                'name': task_name,
                'tt_id': clean_data(record['iUserHandoverDetailsId']),
                'employee_handover_id': clean_data(employee_id_user_handover[0]),
                'user_ids': [(6, 0, interviewer_user_ids)] if interviewer_user_ids else False,
                'project_id': project_id[0] if project_id else False,
                'description': f"Comment: {clean_data(record['txComment'])} \n\n Gitlab URL: {clean_data(record['vGitLabUrl'])} \n\n Description: {clean_data(record['vDescription'])} \n\n Notes: {clean_data(record['vNotes'])}",
            }
            print("----user_handover_data-->", vals)


            existing_ids = models.execute_kw(
                odoo_db,
                uid,
                odoo_password,
                'project.task',
                'search',
                [[
                    ('tt_id', '=', record['iUserHandoverDetailsId']),
                ]]
            )

            #  Update only if the task doesn't exist
            if existing_ids:
                # Update existing record
                models.execute_kw(
                    odoo_db, uid, odoo_password, odoo_model, "write", [existing_ids, vals]
                )
                print(f"Updated record {record['iUserHandoverId']}")
            else:
                # Create new record
                models.execute_kw(odoo_db, uid, odoo_password, odoo_model, "create", [vals])
                print(f"Created new record {record['iUserHandoverId']}")




def main():
    # Connect to Odoo and MySQL
    models, uid = connect_odoo()
    connection = connect_mysql()

    # Define the table name in MySQL and corresponding model in Odoo
    mysql_table = 'user_handover_details'
    odoo_model = 'project.task'

    # Fetch data from MySQL
    mysql_data = fetch_mysql_data(connection, mysql_table)

    # Import data into Odoo
    import_data_to_odoo(models, uid, odoo_model, mysql_data)

if __name__ == "__main__":
    main()
