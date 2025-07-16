# -*- coding: utf-8 -*-
# from odoo import http
from odoo import http
from odoo.http import request
import logging
import base64
import binascii
from odoo.exceptions import AccessError


_logger = logging.getLogger(__name__)


class HrPolicyController(http.Controller):

    @http.route('/hr_policy', type='http', auth='user', website=True)
    def hr_policy(self, **kw):
        if not request.env.user.has_group('base.group_user'):
            raise AccessError("You don't have access to this page.")
        # Set the number of policies per page
        policies_per_page = 10
        
        # Ensure page is an integer and default to 1 if it's not valid
        try:
            page = int(kw.get('page', 1))
        except (ValueError, TypeError):
            page = 1

        # Ensure page is positive
        if page < 1:
            page = 1
        
        total_policies = request.env['hr.policy'].sudo().search_count([('is_published', '=', True),('state', '=', 'approved')])

        if total_policies > 0:
            # Calculate the total number of pages
            total_pages = (total_policies + policies_per_page - 1) // policies_per_page

            # Ensure page is within the range
            if page > total_pages:
                page = total_pages

            # Calculate the offset
            offset = (page - 1) * policies_per_page

            # Fetch the policies for the current page with offset and limit
            policies = request.env['hr.policy'].sudo().search([('is_published', '=', True),('state', '=', 'approved')], offset=offset, limit=policies_per_page)

            # Define the previous and next page numbers
            previous_page = max(page - 1, 1)
            next_page = min(page + 1, total_pages)

            # Create pagination data
            pager = {
                'page': page,
                'total_pages': total_pages,
                'previous': previous_page if page > 1 else None,
                'next': next_page if page < total_pages else None,
                'pages': list(range(1, total_pages + 1)),
            }
        else:
            policies = []
            pager = None

        # Fetch all categories
        categories = request.env['sop.category'].sudo().search([])
        
        # Fetch policies
        policy_list = request.env['hr.policy'].sudo().search([('is_published', '=', True), ('state', '=', 'approved')])
        # Render the template with policies and pagination info (if any)
        return request.render('hr_policy.hr_policy_website_template', {
            'categories': categories,  # Pass categories to the template
            'policy_list': policy_list,  # Pass policies to the template
            'pager': pager,
            'show_policy_snippet': True,  # Set the context variable to show the snippet
            'no_header': True,
            'no_footer': True,
        })


    @http.route('/hr_policy/<model("hr.policy"):policy>', type='http', auth='public', website=True)
    def view_policy(self, policy, page=1, **kwargs):
        policies_per_page = 1  # Policies displayed per page
        try:
            page = int(page)
        except (ValueError, TypeError):
            page = 1

        if page < 1:
            page = 1

        # Fetch all published, approved policies
        domain = [('is_published', '=', True), ('state', '=', 'approved')]
        all_policies = request.env['hr.policy'].sudo().search(domain)

        # Calculate pagination details
        total_policies = len(all_policies)
        total_pages = (total_policies + policies_per_page - 1) // policies_per_page

        if page > total_pages:
            page = total_pages

        offset = (page - 1) * policies_per_page
        policies = all_policies[offset:offset + policies_per_page]

        # Get next and previous policies for navigation
        policy_index = all_policies.ids.index(policy.id) if policy.id in all_policies.ids else -1
        previous_policy = all_policies[policy_index - 1] if policy_index > 0 else None
        next_policy = all_policies[policy_index + 1] if policy_index < total_policies - 1 else None

        pager = {
            'page': page,
            'total_pages': total_pages,
            'previous': page - 1 if page > 1 else None,
            'next': page + 1 if page < total_pages else None,
            'pages': list(range(1, total_pages + 1)),
        }
        category = request.env['hr.policy'].sudo().search(
            ["|", ('name', '=', policy.name), ('policy_id', '=', policy.id)],
            order='version desc'
        )
        return request.render('hr_policy.hr_policy_details_template', {
            'policy': policy,
            'policies': policies,
            'pager': pager,
            'category': category,
            'previous_policy': previous_policy,
            'next_policy': next_policy,
            'no_header': True,
            'no_footer': True,
        })


    @http.route('/get_policy_version', type='json', auth='public', website=True)
    def get_policy_version(self, version_id):
        try:
            # Fetch the policy
            policy = request.env['hr.policy'].sudo().search([('id', '=', version_id)])
            if not policy:
                _logger.error('Policy version not found with ID: %d', policy.version)
                return {'error': 'Policy version not found'}

            data = {
                'description': policy.description or 'No description available',
                # Add other fields if necessary
            }
            return data
        except Exception as e:
            _logger.error(f"Error fetching policy version: {e}")
            return {'error': 'Server error'}

    
    @http.route('/get_policy', type='json', auth='public')
    def get_policies(self):
        policies = request.env['hr.policy'].sudo().search([('is_published', '=', True), ('state', '=', 'approved')])
        print('Debug=================================================:policies', policies)
        policy_data = []
        
        for policy in policies:
            policy_data.append({
                'id': policy.id,
                'name': policy.name,
                'version': policy.version,
                'effective_date': policy.effective_date,
                'sop_category_id': policy.sop_category_id.name,
                'sop_id': policy.sop_category_id.id
            })
        
        return {'policies': policy_data}





