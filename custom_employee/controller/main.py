
from odoo import http
from odoo.addons.survey.controllers import main
from odoo.http import request
from datetime import datetime


class Survey(main.Survey):
    """Inherits the class survey to super the controller"""

    @http.route('/survey/start/<string:survey_token>', type='http',
                auth='public', website=True)
    def survey_start(self, survey_token, answer_token=None, email=False,
                     **post):
        """Inherits the method survey_start to check whether the survey
        appraisal is cancelled, done or has not started"""
        res = super(
            Survey, self).survey_start(
            survey_token=survey_token, answer_token=answer_token, email=email, **post)
        access_data = self._get_access_data(survey_token, answer_token,
                                            ensure_token=False)
        # if access_data.get('answer_sudo').review_id:
        #     if access_data.get('answer_sudo').review_id.status == "Cancel":
        #         return request.render("custom_employee.appraisal_canceled",
        #                               {'survey': access_data.get('survey_sudo')})
        #     elif access_data.get('answer_sudo').review_id.stage_id.name == "Done":
        #         return request.render("custom_employee.appraisal_done",
        #                               {'survey': access_data.get(
        #                                   'survey_sudo')})
        #     elif access_data.get('answer_sudo').review_id.stage_id.name == "To Start":
        #         return request.render("custom_employee.appraisal_draft",
        #                               {'survey': access_data.get(
        #                                   'survey_sudo')})
        return res


class ProbationReviewController(http.Controller):

    @http.route('/review/form/<string:token>', type='http', auth="public", website=True)
    def probation_review_form(self, token, **kw):
        
        # Look for the probation review line with the provided token
        review_line = request.env['employee.probation.review.line'].sudo().search([
            ('token', '=', token),
            ('token_expiry', '>=', datetime.now())
        ],)

        print("============>", review_line)
        if review_line.portal_filled:
            print("============>", review_line)
            return request.redirect('/review/already-submitted')

        if not review_line:
            return request.redirect('/review/expired')

        # Render the review form for the reviewer
        return request.render('custom_employee.probation_review_form_portal', {
            'review': review_line,
            'no_header': True,
            'no_footer': True
        })

    @http.route('/review/submit', type='http', auth="public", methods=['POST'], website=True)
    def submit_probation_review(self, **kw):
        # Look for the probation review line with the provided token

        review_line_id = int(kw.get('review_line_id'))
        review_line = request.env['employee.probation.review.line'].sudo().browse([review_line_id])
                  
        print("============>", review_line)
        if review_line.token_expiry < datetime.now():
            return request.redirect('/review/expired')

        if review_line.portal_filled:
            print("============>1", review_line)
            return request.redirect('/review/already-submitted')

        # Collect all submitted ratings and feedback
        try:
            quality_accuracy = kw.get('quality_accuracy')
            efficiency = kw.get('efficiency')
            attendance = kw.get('attendance')
            time_keeping = kw.get('time_keeping')
            work_relationships = kw.get('work_relationships')
            summary = kw.get('summary')

            # Create tasks
            task_ids = []
            task_count = int(kw.get('task_count', 0))

            for i in range(task_count):
                task_objective = kw.get(f'task_objective_{i}')
                task_feedback = kw.get(f'task_feedback_{i}')
                task_duration = kw.get(f'task_duration_{i}')

                if task_objective and task_feedback and task_duration:
                    task = request.env['probation.review.task'].sudo().create({
                        'review_line_id': review_line.id,
                        'task_objective': task_objective,
                        'task_feedback': task_feedback,
                        'task_duration': task_duration,
                    })
                    task_ids.append(task.id)

            # Create improvements
            improve_ids = []
            improve_count = int(kw.get('task_new_count', 0))

            for i in range(improve_count):
                improve_area = kw.get(f'improve_area_{i}')
                improve_discussion = kw.get(f'improve_discussion_{i}')
                improve_action_by = kw.get(f'improve_action_by_{i}')

                if improve_area and improve_action_by:
                    improve = request.env['probation.review.improve'].sudo().create({
                        'review_line_id': review_line.id,
                        'improve_area': improve_area,
                        'improve_discussion': improve_discussion,
                        'improve_action_by': improve_action_by,
                    })
                    improve_ids.append(improve.id)


            # Update review line with the provided data
            review_line.write({
                'portal_filled': True,
                'quality_accuracy': quality_accuracy,
                'efficiency': efficiency,
                'attendance': attendance,
                'time_keeping': time_keeping,
                'work_relationships': work_relationships,
                'summary': summary,
                'review_status': 'done',
                'task_ids': [(6, 0, task_ids)],  # Linking created tasks
                'improve_ids': [(6, 0, improve_ids)],  # Linking created improvement areas
            })

            # Update the overall probation review
            # review.write({
            #     'quality_accuracy': quality_accuracy,
            #     'efficiency': efficiency,
            #     'attendance': attendance,
            #     'time_keeping': time_keeping,
            #     'work_relationships': work_relationships,
            #     'summary': summary,
            #     'review_status': 'done',
            #     'task_ids': [(6, 0, task_ids)],  # Linking created tasks
            #     'improve_ids': [(6, 0, improve_ids)],  # Linking created improvement areas
            # })

            # Optionally: Notify the HR/Admin team of the submission
            # You can send email notifications here if needed

            # Redirect to a confirmation page
            return request.redirect('/review/thank-you')

        except Exception as e:
            raise UserError(f"Error while submitting the review: {str(e)}")



    @http.route('/review/thank-you', type='http', auth='public', website=True)
    def probation_form_thank_you(self, **kw):
        return request.render('custom_employee.review_form_thank_you', {'no_header': True, 'no_footer': True})

    @http.route('/review/expired', type='http', auth='public', website=True)
    def probation_form_expired(self, **kwargs):
        print("************************7")
        return request.render('custom_employee.employee_review_form_expired_page', {'no_header': True, 'no_footer': True})

    @http.route('/review/already-submitted', type='http', auth='public', website=True)
    def probation_form_already_submitted(self, **kw):
        print("************************8")
        return request.render('custom_employee.review_already_submitted_page', {'no_header': True, 'no_footer': True})
