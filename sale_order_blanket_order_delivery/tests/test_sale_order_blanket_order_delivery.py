# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import freezegun

from odoo import Command
from odoo.exceptions import ValidationError

from .common import SaleOrderBlanketOrderDeliveryCase


class TestSaleOrderBlanketOrderDelivery(SaleOrderBlanketOrderDeliveryCase):
    def test_default_carrier_from_blanket(self):
        self.blanket_so.carrier_id = self.carrier_blanket
        vals = self.blanket_so._get_default_call_off_order_values(self.blanket_so)
        self.assertEqual(vals.get("carrier_id"), self.carrier_blanket.id)

    def test_no_default_carrier_when_blanket_has_none(self):
        vals = self.blanket_so._get_default_call_off_order_values(self.blanket_so)
        self.assertNotIn("carrier_id", vals)

    @freezegun.freeze_time("2025-02-01")
    def test_strict_delivery_method_enforced(self):
        self.blanket_so.carrier_id = self.carrier_blanket
        self.blanket_so.blanket_strict_delivery_method = True
        self.blanket_so.action_confirm()
        order = self.env["sale.order"].create(
            {
                "order_type": "call_off",
                "partner_id": self.partner.id,
                "blanket_order_id": self.blanket_so.id,
                "carrier_id": self.carrier_call_off_1.id,
                "order_line": [
                    Command.create(
                        {"product_id": self.product_1.id, "product_uom_qty": 5.0}
                    ),
                ],
            }
        )
        with self.assertRaisesRegex(
            ValidationError,
            "The delivery method of the call-off order",
        ):
            order.action_confirm()

    @freezegun.freeze_time("2025-02-01")
    def test_strict_delivery_method_ok_when_same_carrier(self):
        self.blanket_so.carrier_id = self.carrier_blanket
        self.blanket_so.blanket_strict_delivery_method = True
        self.blanket_so.action_confirm()
        order = self.env["sale.order"].create(
            {
                "order_type": "call_off",
                "partner_id": self.partner.id,
                "blanket_order_id": self.blanket_so.id,
                "carrier_id": self.carrier_blanket.id,
                "order_line": [
                    Command.create(
                        {"product_id": self.product_1.id, "product_uom_qty": 5.0}
                    ),
                ],
            }
        )
        order.action_confirm()
        self.assertIn(order.state, ["sale", "done"])

    @freezegun.freeze_time("2025-02-01")
    def test_carrier_not_editable_once_call_off_confirmed(self):
        self.blanket_so.carrier_id = self.carrier_blanket
        self.blanket_so.action_confirm()
        order = self.env["sale.order"].create(
            {
                "order_type": "call_off",
                "partner_id": self.partner.id,
                "blanket_order_id": self.blanket_so.id,
                "carrier_id": self.carrier_call_off_1.id,
                "order_line": [
                    Command.create(
                        {"product_id": self.product_1.id, "product_uom_qty": 5.0}
                    ),
                ],
            }
        )
        order.action_confirm()
        with self.assertRaisesRegex(
            ValidationError,
            "cannot be changed once it is confirmed",
        ):
            order.carrier_id = self.carrier_call_off_2.id

    @freezegun.freeze_time("2025-02-01")
    def test_delivery_method_relaxed(self):
        self.blanket_so.carrier_id = self.carrier_blanket
        self.blanket_so.blanket_strict_delivery_method = False
        self.blanket_so.action_confirm()
        order = self.env["sale.order"].create(
            {
                "order_type": "call_off",
                "partner_id": self.partner.id,
                "blanket_order_id": self.blanket_so.id,
                "carrier_id": self.carrier_call_off_1.id,
                "order_line": [
                    Command.create(
                        {"product_id": self.product_1.id, "product_uom_qty": 5.0}
                    ),
                ],
            }
        )
        order.action_confirm()
        self.assertIn(order.state, ["sale", "done"])
