# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    blanket_invoice_call_off_at_own_address = fields.Boolean(
        related="company_id.blanket_invoice_call_off_at_own_address",
        readonly=False,
    )
