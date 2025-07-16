# AKfycbyyhRaJJKt7j6X6SZ0P_crGIir86FYKLMUuvJersesf

import re
import requests
import json
import time

import mimetypes
import base64
import tempfile

import google.generativeai as genai
from PyPDF2 import PdfReader

from odoo import http
from odoo.http import request
from datetime import datetime


genai.configure(api_key='AIzaSyB_oJlFqu9bJpsHt9KsE6oiTdtnXIvYuMU')
model = genai.GenerativeModel('gemini-2.0-flash')

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, '%b %Y').date()
    except Exception:
        return False


class GoogleFormToOdoo(http.Controller):

    @http.route(
        "/google_form_to_odoo", type="json", auth="public", methods=["POST"], csrf=False
    )
    def google_form_to_odoo(self, **post):
        # Extract the form data from the POST request
        data = json.loads(request.httprequest.data)
        print("----data----", data)

        # Create a new lead in the CRM module
        lead_data = {
            "name": data.get("name"),  # Full Name from form
            "contact_name": data.get("name"),  # Full Name from form
            "description": data.get("description"),
            "type": "lead",
        }
        print("----lead_data----", lead_data)

        # Insert the lead into the CRM module
        lead = request.env["crm.lead"].sudo().create(lead_data)

        return {"status": "success", "lead_id": lead.id}


class CandidatePortalController(http.Controller):

    def _get_valid_candidate(self, token):
        candidate = request.env["hr.applicant"].sudo().search([("token", "=", token)], limit=1)
        if not candidate or \
           (candidate.token_expiry and candidate.token_expiry < datetime.now()):
            return None
        return candidate

    @http.route(
        "/candidate/form/<string:token>", type="http", auth="public", website=True
    )
    def candidate_form(self, token, **post):
        print("\n\nDEBUG: Call route /candidate/form/<string:token> \n\n")
        candidate = self._get_valid_candidate(token)
        
        if not candidate:
            return request.redirect('/candidate/evaluation/form/expired')

        if candidate.portal_filled:
            return request.redirect('/candidate/evaluation/form/already-submitted')

        error = request.session.pop('error', None)
        resume_error = request.session.pop('resume_error', None)

        # states = request.env['res.country.state'].sudo().search([])
        return request.render(
            "custom_recruitment.candidate_portal_form_template",
            {"candidate": candidate, "token": token, 'no_header': True, 'no_footer': True, 'error': error, 'resume_error': resume_error},
        )

    @http.route('/candidate/detail/submit', type='json', auth='public', website=True)
    def candidate_form_submit(self, data=None):        
        print("DEBUG: ********* candidate_form_submit *********** /candidate/detail/submit")
        token = data.get('token')
        personal_data = data.get('personal')
        academic_data = data.get('academic')
        professional_data = data.get('professional')
        # family_data = data.get('family')
        
        candidate = request.env["hr.applicant"].sudo().search([("token", "=", token)], limit=1)

        if candidate.portal_filled:
            return {'success': False, 'error': 'Already Submitted'}

        if not candidate:
            return {'success': False, 'error': 'Invalid Token'}

        if academic_data:
            academic_lines = []
            for academic in academic_data:
                degree_record = request.env['hr.recruitment.degree'].sudo().search([('name', '=', academic.get('degree'))], limit=1)
                
                # If the degree doesn't exist, create a new one
                if not degree_record:
                    degree_record = request.env['hr.recruitment.degree'].sudo().create({
                        'name': academic.get('degree'),
                    })
                
                academic_lines.append((0, 0, {
                    'type_id': degree_record.id,
                    'institute_name': academic.get('institute_name'),
                    'pass_year': academic.get('passed_year'),
                    'percentage': academic.get('mark'),
                }))

            # Add the academic lines to the candidate record 
            personal_data['academic_data_ids'] = academic_lines

        # if family_data:
        #     personal_data['family_data_ids'] = [(0, 0, family) for family in family_data]

        if professional_data:
            personal_data['professional_detail_ids'] = [(0, 0, professional) for professional in professional_data]
    
        personal_data['portal_filled'] = True

        candidate.sudo().write(
            personal_data
        )

        return {'success': True}

    @http.route('/candidate/evaluation/thankyou', type='http', auth='public', website=True)
    def candidate_form_thank_you(self, **kwargs):
        return request.render('custom_recruitment.candidate_form_thank_you', {'no_header': True, 'no_footer': True})

    @http.route('/candidate/evaluation/form/already-submitted', type='http', auth='public', website=True)
    def candidate_form_already_submitted(self, **kw):
        return request.render('custom_recruitment.candidate_form_already_submitted_page', {'no_header': True, 'no_footer': True})

    @http.route('/candidate/evaluation/form/expired', type='http', auth='public', website=True)
    def candidate_form_expired(self, **kwargs):
        return request.render('custom_recruitment.candidate_form_expired_page', {'no_header': True, 'no_footer': True})

    def _write_education(self, candidate, education):
        academic_lines = []
        for academic in education:
            degree_name = academic.get('degree')
            degree = request.env['hr.recruitment.degree'].sudo().search([('name', 'ilike', degree_name)], limit=1)
            if not degree:
                degree = request.env['hr.recruitment.degree'].sudo().create({'name': degree_name})
            academic_lines.append((0, 0, {
                'type_id': degree.id,
                'institute_name': academic.get('title') or academic.get('institution'),
                'pass_year': academic.get('dates') or f"{academic.get('start_year')}-{academic.get('end_year')}",
                'percentage': academic.get('Percentage'),
            }))
        if academic_lines:
            candidate.sudo().write({'academic_data_ids': academic_lines})

    def _write_experience(self, candidate, experience, is_linkedin=False):
        experience_lines = []
        for exp in experience:
            entries = exp.get('positions') or [exp] if is_linkedin else [exp]
            
            for item in entries:
                start_date = parse_date(item.get('start_date')) if item.get('start_date') else False
                end_raw = item.get('end_date')
                end_date = parse_date(end_raw) if end_raw and end_raw.lower() != 'present' else False
                experience_lines.append((0, 0, {
                    'company_name': item.get('subtitle') or item.get('company'),
                    'designation': item.get('title') or item.get('position'),
                    'start_date': start_date,
                    'end_date': end_date,
                }))
        if experience_lines:
            candidate.sudo().write({'professional_detail_ids': experience_lines})



    @http.route('/linkedin/candidate/detail/submit', type='http', auth='public', website=True)
    def candidate_linkedin_form_submit(self, **kwargs):
        print("\n\nDEBUG: Call route /linkedin/candidate/detail/submit\n")
        
        token = kwargs.get('token')
        candidate = self._get_valid_candidate(token)

        if not candidate:
            return request.redirect('/candidate/evaluation/form/expired')

        if candidate.portal_filled:
            return request.redirect('/candidate/evaluation/form/already-submitted')
        
        linkedin_url = kwargs.get('linkedin_url')
        
        candidate_data = self._process_brightdata_url(linkedin_url)

        if candidate_data and candidate_data.get('status') == 'failed':
            request.session['error'] = candidate_data.get('error_message')
            return request.redirect(f'/candidate/form/{token}')

        self._write_education(candidate, candidate_data.get('education', []))
        self._write_experience(candidate, candidate_data.get('experience', []), is_linkedin=True)

        candidate.sudo().write({
            'portal_filled': True,
            'current_city': candidate_data.get('city') or candidate.current_city,
        })

        return request.redirect('/candidate/evaluation/thankyou')

    @http.route('/resume/upload/candidate/submit', type='http', auth='public', website=True)
    def candidate_upload_resume_form_submit(self, **kwargs):
        print("\n\nDEBUG: Call route /resume/upload/candidate/submit\n")
        
        token = kwargs.get('token')
        candidate = self._get_valid_candidate(token)

        if not candidate:
            return request.redirect('/candidate/evaluation/form/expired')

        if candidate.portal_filled:
            return request.redirect('/candidate/evaluation/form/already-submitted')
        
        # Step 0: Get the resume file from the request
        resume_file = kwargs.get('resume')
        content = resume_file.read()
        filename = resume_file.filename
        mimetype = mimetypes.guess_type(filename)[0]

        # Step 2: Save PDF temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(content)
            pdf_path = tmp.name

        candidate_data = self.extract_resume_data(pdf_path)

        if candidate_data and candidate_data.get('is_resume') is False:
            request.session['resume_error'] = candidate_data.get('error', 'The uploaded file is not recognized as a resume.') 
            return request.redirect(f'/candidate/form/{token}')

        print("\n\nDEBUG: candidate_data: *************8", candidate_data)

        self._write_education(candidate, candidate_data.get('education', []))
        self._write_experience(candidate, candidate_data.get('experience', []))

        candidate.sudo().write({'portal_filled': True})
        return request.redirect('/candidate/evaluation/thankyou')

    def _is_valid_linkedin_url(self, url):
        # Validate if it's a LinkedIn profile URL
        pattern = r'^https:\/\/(www\.)?linkedin\.com\/in\/[A-Za-z0-9\-_]+\/?$'
        return re.match(pattern, url)

    # Taking the data from BrightData and saving it in Odoo
    def _process_brightdata_url(self, target_url):
        token = request.env['ir.config_parameter'].sudo().get_param('custom_recruitment.bd_token')
        if not token:
            return {'status': 'failed', 'error_message': 'BrightData token is not configured.'}
        dataset_id = request.env['ir.config_parameter'].sudo().get_param('custom_recruitment.bd_dataset_id')
        if not dataset_id:
            return {'status': 'failed', 'error_message': 'BrightData dataset ID is not configured.'}

        # Step 1: Trigger Dataset
        trigger_url = "https://api.brightdata.com/datasets/v3/trigger"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        params = {
            "dataset_id": dataset_id,
            "include_errors": "true",
        }
        payload = [{"url": target_url}]
        print("Triggering BrightData with URL:", target_url)
        response = requests.post(trigger_url, headers=headers, params=params, json=payload)
        print("Trigger response:", response.status_code, response.text)
        response.raise_for_status()

        snapshot_id = response.json().get("snapshot_id")
        print("Snapshot ID received:", snapshot_id)
        if not snapshot_id:
            raise ValueError("No snapshot_id returned from BrightData.")

        # Step 2: Wait until ready
        progress_url = f"https://api.brightdata.com/datasets/v3/progress/{snapshot_id}"
        print("Waiting for data to be ready...")
        while True:
            response = requests.get(progress_url, headers={"Authorization": f"Bearer {token}"})
            print("Progress check:", response.status_code, response.json())
            response.raise_for_status()
            if response.json().get("status") == "ready":
                print("Data is ready!")
                break
            elif response.json().get("status") == "failed":
                return response.json()
                break
            time.sleep(2)

        # Step 3: Fetch snapshot
        snapshot_url = f"https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}"
        params = {"format": "json"}
        print("Fetching snapshot data from:", snapshot_url)
        response = requests.get(snapshot_url, headers={"Authorization": f"Bearer {token}"}, params=params)
        
        print("Progress check:", response.status_code, response.json())
        response.raise_for_status()

        print(response.json())
        
        if response.json()[0].get("status") == "failed":
            print("Data retrieval failed.")
            return response.json()

        full_data = response.json()
        # print(" Raw Data:", full_data)

        # Step 4: Extract useful fields
        extracted = {}
        try:
            profile = full_data[0]

            extracted = {
                "name": profile.get("name"),
                "city": profile.get("city"),
                "country_code": profile.get("country_code"),
                "position": profile.get("position"),
                "current_company": profile.get("current_company"),
                "experience": profile.get("experience", []),
                "education": profile.get("education", []),
                "avatar_url": profile.get("avatar"),
            }

            print("Extracted Fields:", extracted)

        except Exception as e:
           print("Error extracting fields:", str(e))

        return extracted

    def extract_text_from_pdf(self, file_path):
        reader = PdfReader(file_path)
        text = ''
        for page in reader.pages:
            if page.extract_text():
                text += page.extract_text() + '\n'
        return text

    def generate_resume_check_prompt(self, resume_text):
        """Prompt to check if the uploaded file is a resume or CV."""
        return f"""
            Read the text below and answer in JSON format.
            Determine if the document is a resume or CV.

            Respond with:
            {{
                "is_resume": true
            }}

            or

            {{
                "is_resume": false,
                "error": "This does not appear to be a resume or CV."
            }}

            Document Text:
            {resume_text}
        """

    def generate_extraction_prompt(self, resume_text):
        return f"""
            Extract the following structured information from this resume and return it as JSON:

                -   name: The full name of the candidate.
                -   email: The email address of the candidate.
                -   phone: The phone number of the candidate.
                -   education: (list of {{"institution", "degree", "dates", "Percentage"}})
                -   experience: (list of {{"company", "position", "start_date", "end_date"}})
                -   skills: A list of skills.

            Resume Text:
            {resume_text}
        """

    # def extract_resume_data(self, file_path):
    #     resume_text = self.extract_text_from_pdf(file_path)
    #     prompt = self.generate_prompt(resume_text)
    #     response = model.generate_content(prompt)

    #     raw_text = response.candidates[0].content.parts[0].text
    #     cleaned_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text.strip())

    #     print("#################### response::", response)

    #     # Try to parse JSON if Gemini returns clean output
    #     try:
    #         return json.loads(cleaned_text)
    #     except Exception:
    #         print(f"Failed to decode JSON: {e}\nRaw text:\n{cleaned_text}")
    #         raise ValueError(f"Failed to decode JSON: {e}\nRaw text:\n{cleaned_text}")

    def send_prompt(self, prompt):
        """Send prompt to Gemini and clean JSON response."""
        response = model.generate_content(prompt)
        raw_text = response.candidates[0].content.parts[0].text
        cleaned_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text.strip())
        return json.loads(cleaned_text)

    def extract_resume_data(self, file_path):
        """Main method: check if resume, then extract structured data."""
        resume_text = self.extract_text_from_pdf(file_path)

        # Step 1: Validate resume
        check_prompt = self.generate_resume_check_prompt(resume_text)
        try:
            check_result = self.send_prompt(check_prompt)
        except Exception as e:
            print(f"Exception: Resume check failed: {e}")
            print(check_result)
            return check_result

        if check_result and not check_result.get('is_resume', False):
            print("This does not appear to be a resume or CV.", check_result)
            return check_result

        # Step 2: Extract structured data
        extraction_prompt = self.generate_extraction_prompt(resume_text)
        try:
            return self.send_prompt(extraction_prompt)
        except Exception as e:
            raise ValueError(f"Failed to extract resume data: {e}")



    # ************************ Candidate Evaluation ***************************

    @http.route(['/candidate/evaluation/form/<string:token>'], type='http', auth="public", website=True)
    def evaluation_form_token(self, token, **kwargs):
        
        evaluation = request.env['candidate.evaluation'].sudo().search([('token', '=', token)], limit=1)
        
        if evaluation.token_expiry < datetime.now():
            return request.redirect('/candidate/evaluation/form/expired')

        if not evaluation:
            return request.redirect('/candidate/evaluation/form/expired')

        if evaluation.is_filled:
            return request.redirect('/candidate/evaluation/form/already-submitted')

        
        return request.render(
            "custom_recruitment.candidate_evaluation_template",{
                "evaluation": evaluation, 
                'no_header': True, 
                'no_footer': True
            },
        )


    @http.route(['/candidate/evaluation/submit'], type='http', auth="public", website=True, csrf=True)
    def candidate_evaluation_submit(self, **post):
        print("post::======>", post)
        token = post.get('token')
        evaluation = request.env['candidate.evaluation'].sudo().search([('token', '=', token)], limit=1)

        if not evaluation:
            return request.redirect('/candidate/evaluation/form/expired')

        if evaluation.is_filled:
            return request.redirect('/candidate/evaluation/form/already-submitted')

        if not evaluation.is_not_prectical:
            evaluation.write({
                'understanding_position': post.get('position_understanding'),
                'technical_skill': post.get('technical_skills'),
                'logical_skill': post.get('logical_thinking'),
                'communication_skill': post.get('interpersonal_skills'),
                'organizational_fit': post.get('organizational_fit'),
                'attitude': post.get('attitude'),
                'work_culture_fit': post.get('work_culture_fit'),
                'new_learning': post.get('new_learning'),

                'tech_1': post.get('technology_n_1'),
                'tech_1_rating': post.get('technology_1'),
                'tech_2': post.get('technology_n_2'),
                'tech_2_rating': post.get('technology_2'),
                'tech_3': post.get('technology_n_3'),
                'tech_3_rating': post.get('technology_3'),

                'good_points': post.get('good_points'),
                'improvement_points': post.get('improvement_points'),
                'recommendation': post.get('recommendation'),
                'is_not_prectical': True,
            })

            if evaluation.is_not_prectical and evaluation.recommendation != 'practical_assignment':
                evaluation.is_filled = True

        elif evaluation.recommendation == 'practical_assignment' and not evaluation.practical_completed and post.get('practical_recommendation'):
            file_storage = request.httprequest.files.get('task_attachment')
            attachment_binary = base64.b64encode(file_storage.read()) if file_storage else None

            evaluation.write({
                'task_duration': post.get('task_duration'),
                'task_actual_duration': post.get('task_actual_duration'),
                'task_achievement': post.get('task_achievement'),
                'quality_of_work': post.get('quality_of_work'),
                'task_attachment': attachment_binary,
                'good_points_pr': post.get('good_points_pr'),
                'improvement_points_pr': post.get('improvement_points_pr'),
                'recommendation_pr': post.get('practical_recommendation'),
                'practical_completed': True,
            })

            if evaluation.practical_completed and evaluation.recommendation_pr and evaluation.recommendation_pr != 'draft':
                evaluation.is_filled = True
        
        return request.redirect('/candidate/evaluation/thankyou')
