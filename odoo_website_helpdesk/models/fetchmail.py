import imaplib
import logging
import poplib
import socket

from imaplib import IMAP4, IMAP4_SSL
from poplib import POP3, POP3_SSL
from socket import gaierror, timeout
from ssl import SSLError

from datetime import datetime, timedelta

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)
MAX_POP_MESSAGES = 50
MAIL_TIMEOUT = 60


def parse_email_date(raw_email):
    from email.utils import parsedate_to_datetime
    import email
    message = email.message_from_string(raw_email)
    date_header = message.get("Date")
    final_date = parsedate_to_datetime(date_header).strftime('%Y-%m-%d %H:%M:%S')
    date_object = datetime.strptime(final_date, "%Y-%m-%d %H:%M:%S")
    return date_object


class FetchmailServer(models.Model):
    _inherit = 'fetchmail.server'

    company_id = fields.Many2one('res.company', string='Company', required=True)

    def fetch_mail(self):
        """ WARNING: meant for cron usage only - will commit() after each email! """
        additionnal_context = {
            'fetchmail_cron_running': True
        }
        MailThread = self.env['mail.thread']
        for server in self:
            _logger.info('start checking for new emails on %s server %s', server.server_type, server.name)
            additionnal_context['default_fetchmail_server_id'] = server.id
            count, failed = 0, 0
            imap_server = None
            pop_server = None
            connection_type = server._get_connection_type()
            if connection_type == 'imap':
                try:
                    imap_server = server.connect()
                    imap_server.select()

                    # Fetch seen messages from the last 30 minutes (UTC)
                    # print("\nDEBUG: Fetch seen messages from the last 30 minutes (UTC)")
                    date_to_check = server.date + timedelta(hours=5)
                    date_to_check_str = date_to_check.strftime('%d-%b-%Y')
                    search_condition = '(SEEN SINCE "{}")'.format(date_to_check_str)
                    # print("DEBUG: search_condition", search_condition)
                    result, data = imap_server.search(None, search_condition)
                    # print("DEBUG: data", data)

                    for num in data[0].split():
                        res_id = None
                        result, data = imap_server.fetch(num, '(RFC822)')
                        email_date = parse_email_date(data[0][1].decode('utf-8', 'ignore'))  # Parse the email's date
                        # print("DEBUG: email_date", email_date)
                        # print("DEBUG: date_to_check", date_to_check)
                        print("DEBUG: email_date >= date_to_check", email_date >= date_to_check)
                        if email_date >= date_to_check:  # Confirm it falls in the last 30 minutes
                            try:
                                res_id = MailThread.with_context(**additionnal_context).message_process(
                                    server.object_id.model, data[0][1], save_original=server.original,
                                    strip_attachments=(not server.attach)
                                )
                            except Exception:
                                _logger.info('Failed to process mail from %s server %s.', server.server_type, server.name, exc_info=True)
                                failed += 1
                            self._cr.commit()
                            count += 1

                    _logger.info("Fetched SEEN %d email(s) on %s server %s; %d succeeded, %d failed.", count, server.server_type, server.name, (count - failed), failed)

                    # Fetch unseen messages
                    result, data = imap_server.search(None, '(UNSEEN)')
                    for num in data[0].split():
                        res_id = None
                        result, data = imap_server.fetch(num, '(RFC822)')
                        imap_server.store(num, '-FLAGS', '\\Seen')
                        try:
                            res_id = MailThread.with_context(**additionnal_context).message_process(server.object_id.model, data[0][1], save_original=server.original, strip_attachments=(not server.attach))
                        except Exception:
                            _logger.info('Failed to process mail from %s server %s.', server.server_type, server.name, exc_info=True)
                            failed += 1
                        imap_server.store(num, '+FLAGS', '\\Seen')
                        self._cr.commit()
                        count += 1

                    _logger.info("Fetched UNSEEN %d email(s) on %s server %s; %d succeeded, %d failed.", count, server.server_type, server.name, (count - failed), failed)

                
                except Exception:
                    _logger.info("General failure when trying to fetch mail from %s server %s.", server.server_type, server.name, exc_info=True)
                finally:
                    if imap_server:
                        try:
                            imap_server.close()
                            imap_server.logout()
                        except OSError:
                            _logger.warning('Failed to properly finish imap connection: %s.', server.name, exc_info=True)
            elif connection_type == 'pop':
                try:
                    while True:
                        failed_in_loop = 0
                        num = 0
                        pop_server = server.connect()
                        (num_messages, total_size) = pop_server.stat()
                        pop_server.list()
                        for num in range(1, min(MAX_POP_MESSAGES, num_messages) + 1):
                            (header, messages, octets) = pop_server.retr(num)
                            message = (b'\n').join(messages)
                            res_id = None
                            try:
                                res_id = MailThread.with_context(**additionnal_context).message_process(server.object_id.model, message, save_original=server.original, strip_attachments=(not server.attach))
                                pop_server.dele(num)
                            except Exception:
                                _logger.info('Failed to process mail from %s server %s.', server.server_type, server.name, exc_info=True)
                                failed += 1
                                failed_in_loop += 1
                            self.env.cr.commit()
                        _logger.info("Fetched %d email(s) on %s server %s; %d succeeded, %d failed.", num, server.server_type, server.name, (num - failed_in_loop), failed_in_loop)
                        # Stop if (1) no more message left or (2) all messages have failed
                        if num_messages < MAX_POP_MESSAGES or failed_in_loop == num:
                            break
                        pop_server.quit()
                except Exception:
                    _logger.info("General failure when trying to fetch mail from %s server %s.", server.server_type, server.name, exc_info=True)
                finally:
                    if pop_server:
                        try:
                            pop_server.quit()
                        except OSError:
                            _logger.warning('Failed to properly finish pop connection: %s.', server.name, exc_info=True)
            server.write({'date': fields.Datetime.now()})
        return True
