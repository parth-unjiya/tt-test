# -*- coding: utf-8 -*-

import logging
import base64

from odoo import api, fields, models, _
from odoo.tools.misc import clean_context


_logger = logging.getLogger(__name__)


class Attendee(models.Model):
    """ Calendar Attendee Information """
    _inherit = 'calendar.attendee'


    def _send_invitation_emails(self):
        """ Hook to be able to override the invitation email sending process.
         Notably inside appointment to use a different mail template from the appointment type. """
        self._send_mail_to_attendees(
            self.env.ref('calendar.calendar_template_meeting_invitation', raise_if_not_found=False)
        )


    def _send_mail_to_attendees(self, mail_template, force_send=False):
        """ Send mail for event invitation to event attendees.
            :param mail_template: a mail.template record
            :param force_send: if set to True, the mail(s) will be sent immediately (instead of the next queue processing)
        """
        if isinstance(mail_template, str):
            raise ValueError('Template should be a template record, not an XML ID anymore.')
        if self.env['ir.config_parameter'].sudo().get_param('calendar.block_mail') or self._context.get("no_mail_to_attendees"):
            return False
        if not mail_template:
            _logger.warning("No template passed to %s notification process. Skipped.", self)
            return False

        # get ics file for all meetings
        ics_files = self.mapped('event_id')._get_ics_file()

        for attendee in self:
            if attendee.email and attendee._should_notify_attendee():
                event_id = attendee.event_id.id
                ics_file = ics_files.get(event_id)

                # Copy and add template attachments copies to the attendee's email, if available
                attachment_ids = [a.copy({'res_id': 0, 'res_model': 'mail.compose.message'}).id for a in mail_template.attachment_ids]

                if ics_file:
                    context = {
                        **clean_context(self.env.context),
                        'no_document': True, # An ICS file must not create a document
                    }
                    attachment_ids += self.env['ir.attachment'].with_context(context).create({
                        'datas': base64.b64encode(ics_file),
                        'description': 'invitation.ics',
                        'mimetype': 'text/calendar',
                        'res_id': 0,
                        'res_model': 'mail.compose.message',
                        'name': 'invitation.ics',
                    }).ids

                body = mail_template._render_field(
                    'body_html',
                    attendee.ids,
                    compute_lang=True)[attendee.id]
                subject = mail_template._render_field(
                    'subject',
                    attendee.ids,
                    compute_lang=True)[attendee.id]
                attendee.event_id.with_context(no_document=True).sudo().message_notify(
                    email_from=attendee.event_id.user_id.email_formatted or self.env.user.email_formatted,
                    author_id=attendee.event_id.user_id.partner_id.id or self.env.user.partner_id.id,
                    body=body,
                    subject=subject,
                    partner_ids=attendee.partner_id.ids,
                    email_layout_xmlid="custom_recruitment.custom_mail_notification_layout",
                    attachment_ids=attachment_ids,
                    force_send=force_send,
                )