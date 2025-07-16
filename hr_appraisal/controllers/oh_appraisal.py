# -*- coding: utf-8 -*-
from attr import attributes
from odoo import http

from odoo.http import request
from openpyxl.styles.builtins import total
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError


class EmployeeAppraisalController(http.Controller):

    # @http.route('/appraisal/review_form/<string:token>', type='http', auth='user', website=True)
    # def appraisal_review_form(self, **post):
    #     print("\n\nDebug------------------------ kwarg", post)
    #     user = request.env.user
    #     is_manager, is_operational_manager, is_employee = False, False, False
    #     token = post.get('token')
    #     appraisal = request.env['hr.appraisal'].sudo().search([('token', '=', post.get('token'))], limit=1)
    #     print("\n\nDebug------------------------ appraisal", appraisal)
    #     if user.groups_id == request.env.ref('custom_dashboard.group_dashboard_project_manager'):
    #         is_manager = True
    #     elif user.groups_id in [request.env.ref('custom_dashboard.group_dashboard_operation_manager'),
    #                             request.env.ref('custom_dashboard.group_dashboard_admin'),
    #                             request.env.ref('custom_dashboard.group_dashboard_hr'),
    #                             request.env.ref('custom_dashboard.group_dashboard_resource_manager')]:
    #         is_operational_manager = True
    #     else:
    #         is_employee = True

    #     attributes_data = request.env['attribute.attribute'].sudo().search([('active', '=', True)])
    #     print("\n\nDebug------------------------ attributes_data", attributes_data)

    #     def format_experience(start_date):
    #         if not start_date:
    #             return "N/A"
    #         today = datetime.today()
    #         delta = relativedelta(today, start_date)
    #         years = delta.years
    #         months = delta.months
    #         return f"{years} year{'s' if years != 1 else ''} {months} month{'s' if months != 1 else ''}"

    #     def format_time(value):
    #         if not value:
    #             return "N/A"
    #         value_sec = value * 3600
    #         hours = value_sec // 3600
    #         minutes = (value_sec % 3600) // 60
    #         return f"{hours} hour{'s' if hours != 1 else ''} {minutes} minute{'s' if minutes != 1 else ''}"

    #     total_work_experience = format_experience(appraisal.employee_id.carrier_start_date)
    #     company_work_experience = format_experience(appraisal.employee_id.joining_date)
    #     next_appraisal_date = appraisal.employee_id.last_appraisal_date + relativedelta(
    #         years=2) if appraisal.employee_id.last_appraisal_date else datetime.today() + relativedelta(years=1)
    #     print("\n\nDebug------------------------ total_work_experience", total_work_experience, "company_work_experience", company_work_experience)
    #     tasks = request.env['project.task'].sudo().search([('user_ids', '=', appraisal.employee_id.user_id.id)])
    #     print("\n\nDebug------------------------ tasks", tasks)
    #     project_data = {}

    #     for task in tasks:
    #         project = task.project_id
    #         if not project:
    #             continue

    #         project_id = project.id
    #         if project_id not in project_data:
    #             project_data[project_id] = {
    #                 'project_name': project.name,
    #                 'total_task_count': 0,
    #                 'completed_task_count': 0,
    #                 'total_hours_spent': False,
    #             }

    #         project_data[project_id]['total_task_count'] += 1

    #         if task.stage_id and task.state == '1_done':
    #             project_data[project_id]['completed_task_count'] += 1

    #         project_data[project_id]['total_hours_spent'] += task.effective_hours or 0.0

    #     # Convert to a list if needed
    #     project_data_list = list(project_data.values())

    #     print("\n\nDebug------------------------ project_data", project_data_list)
    #     return request.render('hr_appraisal.appraisal_review_form', {
    #                             "appraisal": appraisal,
    #                             "attributes_data": attributes_data,
    #                             "project_data": project_data,
    #                             "next_appraisal_date": next_appraisal_date,
    #                             "total_work_experience": total_work_experience,
    #                             "company_work_experience": company_work_experience,
    #                             "token": token,
    #                             "is_manager": is_manager,
    #                             "is_employee": is_employee,
    #                             "is_operational_manager": is_operational_manager,
    #                             'no_header': True,
    #                             'no_footer': True
    #                         })


    @http.route('/appraisal/review_form/<string:token>', type='http', auth='user', website=True)
    def appraisal_review_form(self, **post):
        print("\n\nDebug------------------------ kwarg", post)
        
        token = post.get('token')
        appraisal = request.env['hr.appraisal'].sudo().search([('token', '=', token)], limit=1)

        is_employee = appraisal.employee_id.user_id.id == request.env.user.id
        is_manager = appraisal.hr_manager_id.user_id.id == request.env.user.id
        is_evaluator = appraisal.hr_collaborator_id.user_id.id == request.env.user.id
        is_technical_evaluator = appraisal.hr_colleague_id.user_id.id == request.env.user.id
        is_mantor = appraisal.employee_id.coach_id.user_id.id == request.env.user.id

        print("\nDEBUG: is_employee", is_employee)
        print("\nDEBUG: is_manager", is_manager)
        print("\nDEBUG: is_evaluator", is_evaluator)
        print("\nDEBUG: is_technical_evaluator", is_technical_evaluator)
        print("\nDEBUG: is_mantor", is_mantor)

        user = request.env.user

        attributes_data = request.env['attribute.attribute'].sudo().search([('active', '=', True)])

        def format_experience(start_date):
            if not start_date:
                return "N/A"
            today = datetime.today()
            delta = relativedelta(today, start_date)
            years = delta.years
            months = delta.months
            return f"{years} year{'s' if years != 1 else ''} {months} month{'s' if months != 1 else ''}"

        def format_time(value):
            if not value:
                return "N/A"
            value_sec = value * 3600
            hours = value_sec // 3600
            minutes = (value_sec % 3600) // 60
            return f"{hours} hour{'s' if hours != 1 else ''} {minutes} minute{'s' if minutes != 1 else ''}"

        total_work_experience = format_experience(appraisal.employee_id.carrier_start_date)
        company_work_experience = format_experience(appraisal.employee_id.joining_date)
        next_appraisal_date = appraisal.employee_id.last_appraisal_date + relativedelta(
            years=2) if appraisal.employee_id.last_appraisal_date else datetime.today() + relativedelta(years=1)
        tasks = request.env['project.task'].sudo().search([('user_ids', '=', appraisal.employee_id.user_id.id)])
        
        project_data = {}
        for task in tasks:
            project = task.project_id
            if not project:
                continue

            project_id = project.id
            if project_id not in project_data:
                project_data[project_id] = {
                    'project_name': project.name,
                    'total_task_count': 0,
                    'completed_task_count': 0,
                    'total_hours_spent': False,
                }

            project_data[project_id]['total_task_count'] += 1

            if task.stage_id and task.state == '1_done':
                project_data[project_id]['completed_task_count'] += 1

            project_data[project_id]['total_hours_spent'] += task.effective_hours or 0.0

        # Convert to a list if needed
        project_data_list = list(project_data.values())

        return request.render('hr_appraisal.appraisal_review_form', {
            "appraisal": appraisal,
            "attributes_data": attributes_data,
            "project_data": project_data,
            "next_appraisal_date": next_appraisal_date,
            "total_work_experience": total_work_experience,
            "company_work_experience": company_work_experience,
            "token": token,
            
            "is_manager": is_manager,
            "is_employee": is_employee,
            "is_evaluator": is_evaluator,
            "is_technical_evaluator": is_technical_evaluator,
            "is_mantor": is_mantor,
            "user": user,
            
            "no_header": True,
            "no_footer": True
        })


    @http.route('/appraisal/submit', type='http', auth='public', methods=['POST'], website=True)
    def appraisal_submit(self, **kwargs):
        print("\n\nDebug-----------------------/appraisal/submit----- kwarg", kwargs)

        try:
            token = kwargs.get('token')
            appraisal = request.env['hr.appraisal'].sudo().search([('token', '=', token)], limit=1) 
            if not appraisal:
                return request.redirect('/appraisal/form/expired')

            # Get the user submitting the form
            current_user = request.env.user
            is_employee = current_user.id == appraisal.employee_id.user_id.id

            # Get or create appraisal data record
            appraisal_data = request.env['hr.appraisal.data'].sudo().search([
                ('appraisal_id', '=', appraisal.id)
            ], limit=1)

            if not appraisal_data:
                appraisal_data = request.env['hr.appraisal.data'].sudo().create({
                    'name': f'Appraisal Data for {appraisal.employee_id.name}',
                    'appraisal_id': appraisal.id,
                })

            # Redirect employee if they already submitted their part
            if is_employee:
                if appraisal_data.last_goals_ids or appraisal_data.future_goals_ids:
                    return request.redirect('/appraisal/form/already-submitted')

            if kwargs.get('is_evaluator') and appraisal_data.goals_notes_ids:
                return request.redirect('/appraisal/form/already-submitted')

            # === LAST GOALS SECTION ===
            if is_employee and not appraisal_data.last_goals_ids:
                last_goals_ids = []
                i = 1
                while True:
                    desc = kwargs.get(f'goal_description_{i}')
                    action = kwargs.get(f'goal_action_{i}')
                    complete = kwargs.get(f'goal_completed_{i}')
                    if not desc and not action:
                        break
                    if desc and action:
                        goal = request.env['last.evaluation.goal'].sudo().create({
                            'name': desc,
                            'action_taken': action,
                            'is_completed': complete,
                            'portal_filled': True,
                        })
                        last_goals_ids.append(goal.id)
                    i += 1
                if last_goals_ids:
                    appraisal_data.write({'last_goals_ids': [(6, 0, last_goals_ids)]})

            # === FUTURE GOALS SECTION ===
            if is_employee and not appraisal_data.future_goals_ids:
                future_goals_ids = []
                i = 1
                while True:
                    desc = kwargs.get(f'goal_description_future_{i}')
                    action = kwargs.get(f'goal_action_future_{i}')
                    time = kwargs.get(f'estimated_time_future_{i}')
                    if not desc and not action:
                        break
                    if desc and action:
                        future_goal = request.env['future.evaluation.goal'].sudo().create({
                            'name': desc,
                            'action_needs': action,
                            'estimation_time': time,
                            'portal_filled': True,
                        })
                        future_goals_ids.append(future_goal.id)
                    i += 1
                if future_goals_ids:
                    appraisal_data.write({'future_goals_ids': [(6, 0, future_goals_ids)]})

            # === Additional Points Section ===
            if not appraisal_data.additional_point and kwargs.get('additional_points'):
                appraisal_data.write({'additional_point': kwargs.get('additional_points')})


            if kwargs.get('rating_emp_id'):
                rating_emp_id = request.env['hr.employee'].sudo().browse(int(kwargs.get('rating_emp_id')))
                
                # === ATTRIBUTE RATINGS SECTION ===
                attribute_data_ids = []
                for key, value in kwargs.items():

                    if key == 'rating_emp_id':
                        continue
                    
                    if key.startswith('rating_'):
                        attr_id = int(key.split('_')[1])
                        rating = int(value)
                        comment = kwargs.get(f'comment_{attr_id}', '')

                        # Find or create the attribute_data for this attribute under this appraisal
                        attribute_data = request.env['attribute.data'].sudo().search([
                            ('attribute_id', '=', attr_id),
                            ('appraisal_data_id', '=', appraisal_data.id),
                        ], limit=1)


                        if not attribute_data:
                            attribute_data = request.env['attribute.data'].sudo().create({
                                'attribute_id': attr_id,
                                'appraisal_data_id': appraisal_data.id,
                            })

                        print("\nDEBUG: attribute_data", attribute_data)

                        # Check if this manager already filled for this attribute
                        existing_rating = request.env['attribute.manager.rating'].sudo().search([
                            ('attribute_id', '=', attr_id),
                            ('employee_id', '=', rating_emp_id.id),
                            ('attribute_data_id', '=', attribute_data.id),
                        ], limit=1)

                        if existing_rating:
                            return request.redirect('/appraisal/form/already-submitted')

                        if not existing_rating:
                            existing_rating = request.env['attribute.manager.rating'].sudo().create({
                                'attribute_data_id': attribute_data.id,
                                'attribute_id': attr_id,
                                'employee_id': rating_emp_id.id,
                                'rating': rating,
                                'notes': comment,
                            })

                            print(f"\nDEBUG: New rating created for manager {rating_emp_id.name} with rating {rating} and comment {comment}")

                        print("\nDEBUG: existing_rating", existing_rating)
                        attribute_data_ids.append(attribute_data.id)

                if attribute_data_ids:
                    appraisal_data.write({'attribute_data_ids': [(6, 0, attribute_data_ids)]})


            # === GOALS NOTES BY EVALUATOR ===
            if kwargs.get('is_evaluator') and not appraisal_data.goals_notes_ids:
                goal_notes = []
                i = 1
                while True:
                    goal_name = kwargs.get(f'goal_{i}')
                    note = kwargs.get(f'goal_notes_{i}')
                    if not goal_name and not note:
                        break
                    if goal_name and note:
                        note_rec = request.env['goals.notes.evalutor'].sudo().create({
                            'name': goal_name,
                            'note': note,
                            'appraisal_data_id': appraisal_data.id,
                        })
                        goal_notes.append(note_rec.id)
                    i += 1

                if goal_name:
                    appraisal_data.write({'goals_notes_ids': [(6, 0, goal_notes)]})
                    
                    if kwargs.get('additional_comments'):
                        appraisal_data.write({'comment': kwargs.get('additional_comments')})

            return request.redirect('/appraisal/thankyou')

        except Exception as e:
            raise UserError(f"Error while submitting the appraisal: {str(e)}")


    @http.route('/appraisal/thankyou', type='http', auth='public', website=True)
    def candidate_form_thank_you(self, **kwargs):
        return request.render('hr_appraisal.appraisal_form_thank_you', {'no_header': True, 'no_footer': True})

    @http.route('/appraisal/form/already-submitted', type='http', auth='public', website=True)
    def candidate_form_already_submitted(self, **kw):
        return request.render('hr_appraisal.appraisal_form_already_submitted_page', {'no_header': True, 'no_footer': True})

    @http.route('/appraisal/form/expired', type='http', auth='public', website=True)
    def candidate_form_expired(self, **kwargs):
        return request.render('hr_appraisal.appraisal_form_expired_page', {'no_header': True, 'no_footer': True})
