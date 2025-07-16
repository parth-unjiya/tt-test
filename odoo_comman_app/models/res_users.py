import logging

from odoo import _, api, fields, models
from odoo.http import request
from odoo.exceptions import UserError, ValidationError


_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    def _change_password(self, new_passwd):
        new_passwd = new_passwd.strip()
        if not new_passwd:
            raise UserError(
                _("Setting empty passwords is not allowed for security reasons!")
            )

        if len(new_passwd) < 8:
            raise UserError(_("The password must be at least 8 characters long."))

        ip = request.httprequest.environ["REMOTE_ADDR"] if request else "n/a"

        _logger.info(
            "Password change for %r (#%d) by %r (#%d) from %s",
            self.login,
            self.id,
            self.env.user.login,
            self.env.user.id,
            ip,
        )

        self.password = new_passwd
