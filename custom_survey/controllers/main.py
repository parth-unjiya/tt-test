
import difflib
from odoo.addons.survey.controllers.main import Survey
from odoo import http
from odoo.http import request


class SurveyCustom(Survey):

    # FIELD_MAPPING = {
    #     "mobile number": "mobile",
    #     "email address": "email",
    #     "full name": "name",
    #     "country": "country_id",
    #     'source': 'source_id',
    #     "gender": "gender"
    # }

    # @http.route('/survey/submit/<string:survey_token>/<string:answer_token>', type='json', auth='public', website=True)
    # def survey_submit(self, survey_token, answer_token, **post):
    #     """ Submit a page from the survey.
    #     This will take into account the validation errors and store the answers to the questions.
    #     If the time limit is reached, errors will be skipped, answers will be ignored and
    #     survey state will be forced to 'done'.
    #     Also returns the correct answers if the scoring type is 'scoring_with_answers_after_page'."""
    #     # Survey Validation
    #     access_data = self._get_access_data(survey_token, answer_token, ensure_token=True)
    #     print("----access_data----", access_data)

    @http.route('/survey/submit/<string:survey_token>/<string:answer_token>', type='json', auth='public', website=True)
    def survey_submit(self, survey_token, answer_token, **post):

        # Custom logic goes here
        print("----Custom Survey Submit Override----")

        # Call the original method (if needed)
        response = super(SurveyCustom, self).survey_submit(survey_token, answer_token, **post)
        print('post-------------------', post)
        access_data = self._get_access_data(survey_token, answer_token, ensure_token=True)
        survey_sudo, answer_sudo = access_data['survey_sudo'], access_data['answer_sudo']
        # Create a new record in the hr.applicant.call model
        # questions, page_or_question_id = survey_sudo._get_survey_questions(answer=answer_sudo,
        #                                                                    page_id=post.get('page_id'),
        #
        #                                                                    question_id=post.get('question_id'))
        # post_name=request.env['survey.question'].sudo().browse(post.get('question_id'))
        # for post1 in post_name:
        #     print("**post_name", post1.display_name)
        # print("**post_name", post[0])
        questions, page_or_question_id = survey_sudo._get_survey_questions(answer=answer_sudo,
                                                                           page_id=post.get('page_id'),
                                                                           question_id=post.get('question_id'))
        print("----questions----", questions)
        print("**answer_sudo.user_input_line_ids", answer_sudo.user_input_line_ids.read())
        question_types = set(question['question_type'] for question in questions)

        print("----question_types----", question_types)

        if survey_sudo.is_candidate_form_create and answer_sudo.state == 'done':
            custom_dict = {}
            for item in answer_sudo.user_input_line_ids:

                print("----item['answer_type']----", item.read())
                question_id = item['question_id'].display_name
                if item['answer_type'] == 'char_box':
                    value = item['value_char_box']
                elif item['answer_type'] == 'numerical_box':
                    value = item['value_numerical_box']
                elif item['answer_type'] == 'simple_choice':
                    value = item['value_simple_choice']
                elif item['answer_type'] == 'suggestion':
                    value = item.suggested_answer_id.value
                else:
                    value = None  # Hand
                custom_dict[question_id] = value

            print('=======custom_dict=====', custom_dict)

            model_obj = request.env['hr.applicant.call']
            model_fields = model_obj.fields_get()
            field_mapping = {field.lower(): field for field in model_fields.keys()}
            print("\nDebug===========================field_mapping:", field_mapping)
            mapped_data = {}
            for key, value in custom_dict.items():
                normalized_key = key.lower().strip()
                field_name = field_mapping.get(normalized_key)
                if not field_name:
                    closest_match = difflib.get_close_matches(normalized_key, field_mapping.keys(), n=1, cutoff=0.6)
                    field_name = closest_match[0] if closest_match else None
                if field_name:
                    field_type = model_fields[field_name].get('type', '')
                    if field_type == 'many2one':
                        related_model = model_fields[field_name]['relation']
                        value = self._get_many2one_id(related_model, value)
                    elif field_type == 'selection':
                        selection_values = [item[0] for item in model_fields[field_name]['selection']]
                        value = self._get_selection_value(selection_values, value)
                    if isinstance(value, tuple) and len(value) == 2:
                        value = self._clean_survey_value(value)
                    mapped_data[field_name] = value

            if "mobile" not in mapped_data:
                print("⚠️ Mobile number not mapped. Check field names!")
            print("\nDebug===========================mapped_data:", mapped_data)

            if mapped_data:
                record = model_obj.create(mapped_data)  # Save mapped data
                print("\nDebug===========================record:", record)
        return response

    def _get_many2one_id(self, related_model, value):
        """
        Finds the ID of a Many2one field based on its name.

        :param related_model: The related model name (e.g., 'res.country')
        :param value: The name of the record (e.g., 'United States')
        :return: The ID of the record or None
        """
        related_obj = request.env[related_model]
        record = related_obj.search([('name', '=ilike', value)], limit=1)
        print("\nDebug===========================record:", record)
        return record.id if record else None

    def _get_selection_value(self, selection_values, value):
        """
        Matches a survey response value to a valid selection field value.

        :param selection_values: List of valid selection values
        :param value: User input from the survey
        :return: Matched selection value or None
        """
        closest_match = difflib.get_close_matches(value.lower(), [v.lower() for v in selection_values], n=1, cutoff=0.7)
        if closest_match:
            return next((v for v in selection_values if v.lower() == closest_match[0]), None)
        return None
