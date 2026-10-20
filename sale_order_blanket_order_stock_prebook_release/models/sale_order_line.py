# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_procurement_values(self):
        values = super()._prepare_procurement_values()
        order = self.order_id
        if (
            order.order_type == "blanket"
            and order.blanket_reservation_strategy == "at_confirm"
        ):
            values["date_priority"] = order.blanket_move_date_priority
        return values
