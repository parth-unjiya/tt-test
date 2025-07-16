import xmlrpc.client

# Odoo connection details
odoo_url = "https://tingtong.spaceo.in/xmlrpc/2"
odoo_db = "tingtong_v1"
odoo_username = "admin@admin.com"
odoo_password = "ur48x"

def connect_odoo():
    """Connect to Odoo via XML-RPC."""
    common = xmlrpc.client.ServerProxy(f"{odoo_url}/common")
    uid = common.authenticate(odoo_db, odoo_username, odoo_password, {})
    if not uid:
        raise Exception("❌ Failed to authenticate with Odoo")
    models = xmlrpc.client.ServerProxy(f"{odoo_url}/object")
    print("✅ Connected to Odoo")
    return models, uid

def link_applicant_to_calls(models, uid):
    """Link hr.applicant.call to hr.applicant based on email and phone."""
    
    # Step 1: Get all hr.applicant.call with no applicant_id
    call_ids = models.execute_kw(
        odoo_db, uid, odoo_password,
        'hr.applicant.call', 'search',
        [['|', ('applicant_id', '=', False), ('is_applicant', '=', False)]]
    )

    if not call_ids:
        print("✅ No call records to link.")
        return

    call_records = models.execute_kw(
        odoo_db, uid, odoo_password,
        'hr.applicant.call', 'read',
        [call_ids],
        {'fields': ['id', 'email', 'mobile']},
    )

    print(f"🔍 Found {len(call_records)} call records to check...")

    for call in call_records:
        email = call.get('email')
        mobile = call.get('mobile')

        if not email or not mobile:
            print(f"⚠️ Skipping call ID {call['id']} (missing email or mobile)")
            continue

        # Step 2: Search applicant with matching email and mobile
        applicant_ids = models.execute_kw(
            odoo_db, uid, odoo_password,
            'hr.applicant', 'search',
            [[
                ('email_from', '=', email),
                ('partner_mobile', '=', mobile)
            ]],
            {'limit': 1}
        )

        if applicant_ids:
            models.execute_kw(
                odoo_db, uid, odoo_password,
                'hr.applicant.call', 'write',
                [[call['id']], {'applicant_id': applicant_ids[0], 'is_applicant': True}]
            )
            print(f"✅ Linked call ID {call['id']} → applicant ID {applicant_ids[0]}")
        else:
            print(f"❌ No match found for call ID {call['id']} (email: {email}, mobile: {mobile})")

def main():
    models, uid = connect_odoo()
    link_applicant_to_calls(models, uid)

if __name__ == "__main__":
    main()
