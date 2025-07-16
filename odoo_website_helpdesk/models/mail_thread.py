from odoo import models, fields, api
import re

class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        """Called by ``message_process`` when a new message is received
           for a given thread model, if the message did not belong to
           an existing thread.
           The default behavior is to create a new record of the corresponding
           model (based on some very basic info extracted from the message).
           Additional behavior may be implemented by overriding this method.

           :param dict msg_dict: a map containing the email details and
                                 attachments. See ``message_process`` and
                                ``mail.message.parse`` for details.
           :param dict custom_values: optional dictionary of additional
                                      field values to pass to create()
                                      when creating the new thread record.
                                      Be careful, these values may override
                                      any other values coming from the message.
           :rtype: int
           :return: the id of the newly created thread object
        """
        data = {}
        recipient = msg_dict.get('recipients')
        to = msg_dict.get('to')
        server_object = self.env['fetchmail.server'].search(['|', ('user', '=', recipient), ('user', '=', to)])
        if not server_object:
            print("-------------------------------recipient", recipient, "-----\n\n", to)
            email = re.findall(r'<([^>]+)>', recipient if recipient else to)[0]
            server_object = self.env['fetchmail.server'].search([('user', '=', email)])
        print("-------------------------------server_object", server_object)
        if isinstance(custom_values, dict):
            data = custom_values.copy()
        model_fields = self.fields_get()
        name_field = self._rec_name or 'name'
        if name_field in model_fields and not data.get('name'):
            data[name_field] = msg_dict.get('subject', '')

        primary_email = self._mail_get_primary_email_field()
        if primary_email and msg_dict.get('email_from'):
            data[primary_email] = msg_dict['email_from']

        stage_field = 'stage_id'
        if stage_field in model_fields and not data.get('stage_id'):
            data[stage_field] = self.env.ref('odoo_website_helpdesk.stage_inbox').id

        company_field = 'company_id'
        if company_field in model_fields and not data.get('company_id'):
            data[company_field] = server_object.company_id.id

        return self.create(data)