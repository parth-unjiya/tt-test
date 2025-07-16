# -*- coding: utf-8 -*-

from odoo import api, models, fields


class MailTemplate(models.Model):
    _inherit = "mail.template"

    def send_mail(
        self,
        res_id,
        force_send=False,
        raise_exception=False,
        email_values=None,
        email_layout_xmlid=False,
    ):
        self.ensure_one()

        config = self.env["ir.config_parameter"].sudo()
        cc_emails = config.get_param("odoo_comman_app.cc_emails") or ""
        to_emails = config.get_param("odoo_comman_app.to_emails") or ""
        cc_templates = config.get_param("odoo_comman_app.cc_templates") or ""

        template_ids = [int(tid) for tid in cc_templates.split(",") if tid.strip()]
        email_values = email_values or {}

        if self.id in template_ids:
            # Combine CC emails
            cc_set = set()
            for source in [self.email_cc or "", cc_emails, email_values.get("email_cc", "")]:
                cc_set.update(email.strip() for email in source.split(",") if email.strip())
            if cc_set:
                email_values["email_cc"] = ", ".join(sorted(cc_set))    


        # Combine TO emails
        if self.id and not self.email_to:
            to_set = set()
            for source in [self.email_to or "", to_emails, email_values.get("email_to", "")]:
                to_set.update(email.strip() for email in source.split(",") if email.strip())
            if to_set:
                email_values["email_to"] = ", ".join(sorted(to_set))
            
        return super(MailTemplate, self).send_mail(
            res_id,
            force_send=force_send,
            raise_exception=raise_exception,
            email_values=email_values,
            email_layout_xmlid=email_layout_xmlid,
        )
