import base64
import csv
import os
import io

from datetime import datetime, timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class UploadFileWizard(models.TransientModel):
    _name = "upload.file.wizard"
    _description = "Upload File and Update Attendees"

    upload_file = fields.Binary(string="Upload File", attachment=True)


    def update_attendees(self):
        if not self.upload_file:
            raise UserError(_("Please upload a file."))
        try:
            decoded_data = base64.b64decode(self.upload_file)
            decoded_text = decoded_data.decode('utf-8-sig', errors='ignore')
            lines = decoded_text.splitlines()

            print("\nTotal lines:", len(lines))

            # Step 1: Find the line that starts with 'Date' as header
            header_index = -1
            for i, line in enumerate(lines):
                if line.strip().startswith('Date'):
                    header_index = i
                    break

            if header_index == -1:
                raise UserError(_("Could not find the CSV header row."))

            # print(f"Found header at line {header_index}: {repr(lines[header_index])}")

            # Step 2: Read from header onward
            relevant_lines = lines[header_index:]
            csv_data = "\n".join(relevant_lines)

            csv_file = io.StringIO(csv_data)
            reader = csv.reader(csv_file)

            # Get the header row and normalize it (remove empty headers)
            header = next(reader)
            # print("Raw Header:", header)

            # Generate fake field names if some are blank
            final_header = [
                h.strip() if h.strip() else f'col_{i}' for i, h in enumerate(header)
            ]

            # print("Final Header:", final_header)

            for row in reader:
                if not any(row):
                    continue  # Skip empty rows

                row_dict = dict(zip(final_header, row))
                # print("Parsed Row:", row_dict)

                status = row_dict.get('Status') or row_dict.get('col_23')
                print(repr(status))
                if status != 'P':
                    continue

                # Example: search and update using code and name
                data = row_dict.get('Date') or row_dict.get('col_1')
                emp_code = row_dict.get('Emp. Code') or row_dict.get('col_4')
                name = row_dict.get('Name') or row_dict.get('col_5')

                print(repr(data))
                # print(repr(emp_code))
                # print(repr(name))

                data_date = datetime.strptime(data, '%d/%m/%Y')
                start_dt = data_date.replace(hour=0, minute=0, second=0)
                end_dt = start_dt + timedelta(days=1)

                # print(repr(data_date))
                # print(repr(start_dt))
                # print(repr(end_dt))

                # input("Press Enter to continue...")

                if emp_code and data:
                    attendee = self.env['hr.attendance'].sudo().search([
                        ('employee_id.emp_code', '=', emp_code),
                        ('create_date', '>=', start_dt),
                        ('create_date', '<', end_dt),
                    ], limit=1)

                    time_str_one = row_dict.get('col_11')
                    time_str_two = row_dict.get('col_14')
                    print(repr(time_str_one))
                    print(repr(time_str_two))

                    combined_punch_in_datetime = datetime.strptime(f"{data} {time_str_one}", "%d/%m/%Y %H:%M")
                    combined_punch_out_datetime = datetime.strptime(f"{data} {time_str_two}", "%d/%m/%Y %H:%M")

                    print("emp_code:", emp_code)
                    print("Attendee:", attendee)

                    if attendee:
                        # Just an example — map your own fields
                        attendee.write({
                            'punch_in': combined_punch_in_datetime - timedelta(hours=5, minutes=30),
                            'punch_out': combined_punch_out_datetime - timedelta(hours=5, minutes=30),
                        })
                    print("\n========Updated==========\n")
        except Exception:
            raise UserError(_("Invalid file. Please upload a valid file."))

        return {'type': 'ir.actions.act_window_close'}

