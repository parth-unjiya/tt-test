
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
    for record in data:
        # Search for the existing appraisal by its tt_id
        appraisal_id = models.execute_kw(odoo_db, uid, odoo_password, 'hr.appraisal', 'search', [[('tt_id', '=', record['iAppraisalId'])]])
        print('\n\nappraisal_id', appraisal_id)
        
        # Search for the reviewer(s) based on iReviewerId in hr.employee
        reviewer_ids = models.execute_kw(odoo_db, uid, odoo_password, 'hr.employee', 'search', [[('tt_id', '=', record['iReviewerId'])]])
        print('reviewer_ids', reviewer_ids)
        
        if appraisal_id:
            # Fetch the current hr_manager_ids from the existing appraisal
            existing_manager_ids = models.execute_kw(
                odoo_db, uid, odoo_password, 'hr.appraisal', 'read', [appraisal_id], {'fields': ['hr_manager_ids']}
            )[0]['hr_manager_ids']
            
            # Ensure reviewers are added as manager IDs (without duplicates)
            if reviewer_ids:
                # Add the reviewer(s) to the existing manager IDs
                updated_manager_ids = list(set(existing_manager_ids + reviewer_ids))
            else:
                # If no reviewers found, keep the existing managers
                updated_manager_ids = existing_manager_ids
            
            # Prepare the data to be updated in Odoo
            appraisal_reviers_data = {
                'hr_manager_ids': [(6, 0, updated_manager_ids)],  # Use Odoo's many2many syntax
            }
            print('appraisal_reviers_data', appraisal_reviers_data)

            # Execute the write command to update the appraisal record
            result = models.execute_kw(
                odoo_db, uid, odoo_password, 'hr.appraisal', 'write', [appraisal_id, appraisal_reviers_data]
            )
            print('\nUpdated appraisal record:', result)




def main():
    # Connect to Odoo and MySQL
    models, uid = connect_odoo()
    connection = connect_mysql()

    # Define the table name in MySQL and corresponding model in Odoo
    mysql_table = 'appraisal_reviewers'
    odoo_model = 'hr.appraisal'

    # Fetch data from MySQL
    mysql_data = fetch_mysql_data(connection, mysql_table)

    # Import data into Odoo
    import_data_to_odoo(models, uid, odoo_model, mysql_data)

if __name__ == "__main__":
    main()
