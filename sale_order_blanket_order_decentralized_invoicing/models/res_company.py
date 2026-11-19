# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    blanket_invoice_call_off_at_own_address = fields.Boolean(
        string="Invoice Call-offs at their Addresses",
        help="Default value of the option on new blanket orders. When checked, "
        "the delivered quantities of a call-off order with other invoice or "
        "shipping addresses than its blanket order are invoiced at the "
        "addresses of the call-off order.",
    )
