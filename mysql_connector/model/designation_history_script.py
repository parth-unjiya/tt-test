
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
        employee_id = models.execute_kw(odoo_db, uid, odoo_password, 'hr.employee', 'search', [[('tt_id', '=', record['iUserId'])],])
        # record=models.execute_kw(odoo_db, uid, odoo_password, 'hr.employee', 'read', [employee_id], {'fields': ['promotion_history_ids']})
        if employee_id:
            def format_date(date_value):
                if isinstance(date_value, (datetime, date)):
                    return date_value.strftime('%Y-%m-%d')  # Format the date properly
                return None  # Use None if the date is invalid or None

            # Extract and format the start and end dates
            start_date = format_date(record.get('dStartDate'))  # '2022-04-12'
            end_date = format_date(record.get('dEndDate'))      # None in your case

            # Log the start_date and end_date values for debugging
            print('start_date:', start_date, 'end_date:', end_date)

            # Prepare the promotion data, exclude date fields if they are None
            promotion_data = {
                'employee_id': employee_id,
                'department_id': record['iDepartmentMasterId'],
                'sub_designation_id': record['iSubDesignationMasterId'],
                'designation_id': record['iDesignationMasterId']
            }

            # Only add dates if they are not None
            if start_date is not None:
                promotion_data['start_date'] = start_date
            if end_date is not None:
                promotion_data['end_date'] = end_date

            # Execute the write command
            record1 = models.execute_kw(
                odoo_db,
                uid,
                odoo_password,
                'hr.employee',
                'write',
                [employee_id, {'promotion_history_ids': [(0, 0, promotion_data)]}]
            )
            print('\n\nemployee_id:', record1)

        # if employee_id:
        #     # Update existing record
        #     models.execute_kw(odoo_db, uid, odoo_password, 'hr.partner', 'write', [employee_id, vals])
        #     print(f"Updated record {record['vDesignationName']}")
        # else:
        #     # Create new record
        #     if vals:
        #         models.execute_kw(odoo_db, uid, odoo_password, odoo_model, 'create', [vals])
        #         print(f"Created new record {record['vDesignationName']}")


def main():
    # Connect to Odoo and MySQL
    models, uid = connect_odoo()
    connection = connect_mysql()

    # Define the table name in MySQL and corresponding model in Odoo
    mysql_table = 'user_designation_history'
    odoo_model = 'hr.employee.promotion'

    # Fetch data from MySQL
    mysql_data = fetch_mysql_data(connection, mysql_table)

    # Import data into Odoo
    import_data_to_odoo(models, uid, odoo_model, mysql_data)

if __name__ == "__main__":
    main()
