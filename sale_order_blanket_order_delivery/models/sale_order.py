# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.sale.models.sale_order import LOCKED_FIELD_STATES


class SaleOrder(models.Model):
    _inherit = "sale.order"

    blanket_strict_delivery_method = fields.Boolean(
        string="Strict Delivery Method?",
        help="If checked, the system will enforce that the call-off orders use "
        "the same delivery method (carrier) as the one defined on the blanket "
        "order. If not checked, the delivery method defined on the blanket "
        "order is only used as a default value when creating a call-off order "
        "and can then be freely changed on the call-off order.",
        states=LOCKED_FIELD_STATES,
        tracking=True,
    )

    @api.constrains("order_type", "blanket_order_id", "carrier_id", "state")
    def _check_call_off_delivery_method(self):
        for order in self:
            if order.state != "sale":
                continue
            if (
                order.order_type != "call_off"
                or order.blanket_order_id.order_type != "blanket"
            ):
                continue
            blanket_order = order.blanket_order_id
            if (
                blanket_order.blanket_strict_delivery_method
                and order.carrier_id != blanket_order.carrier_id
            ):
                raise ValidationError(
                    _(
                        "The delivery method of the call-off order %(order)s "
                        "must be the same as the one defined on the blanket "
                        "order %(blanket_order)s.",
                        order=order.name,
                        blanket_order=blanket_order.name,
                    )
                )

    def _check_call_off_carrier_editable(self, vals):
        # Once a call-off order is confirmed, its stock moves/reservations
        # are already created against the blanket order line (see
        # sale_order_blanket_order). Changing the delivery method afterwards
        # would leave those moves out of sync with the new carrier, and
        # there is no supported way to unwind/relaunch them for that. We
        # fail fast with a clear message instead of silently leaving a
        # delivery line stuck on the call-off order (see
        # ``_on_call_off_order_confirm``).
        if "carrier_id" not in vals:
            return
        for order in self:
            if order.order_type == "call_off" and order.state in ("sale", "done"):
                raise ValidationError(
                    _(
                        "The delivery method of the call-off order %(order)s "
                        "cannot be changed once it is confirmed.",
                        order=order.name,
                    )
                )

    def write(self, values):
        self._check_call_off_carrier_editable(values)
        return super().write(values)

    def _get_default_call_off_order_values(self, blanket_order_id):
        vals = super()._get_default_call_off_order_values(blanket_order_id)
        if blanket_order_id.carrier_id:
            vals["carrier_id"] = blanket_order_id.carrier_id.id
        return vals

    def _on_call_off_order_confirm(self):
        # Move any delivery lines from the call-off order to the blanket order.
        # This is required since the invoicing and delivery costs are managed on
        # the blanket order, not the call-off order.
        # This must happen before calling super(), which (through
        # ``_link_lines_to_blanket_order_line``) tries to match every
        # call-off order line against the blanket order lines
        for order in self:
            delivery_lines = order.order_line.filtered("is_delivery")
            if delivery_lines:
                delivery_lines.order_id = order.blanket_order_id
        return super()._on_call_off_order_confirm()
