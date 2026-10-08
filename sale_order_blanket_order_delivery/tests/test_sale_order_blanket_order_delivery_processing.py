# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import freezegun

from odoo import Command

from .common import SaleOrderBlanketOrderDeliveryCase


class TestSaleOrderBlanketOrderDeliveryProcessing(SaleOrderBlanketOrderDeliveryCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.blanket_so.carrier_id = cls.carrier_blanket
        cls.blanket_so.action_confirm()

    def _create_call_off_order(self, product_uom_qty, carrier_id, commitment_date):
        return self.env["sale.order"].create(
            {
                "order_type": "call_off",
                "partner_id": self.partner.id,
                "blanket_order_id": self.blanket_so.id,
                "carrier_id": carrier_id,
                "commitment_date": commitment_date,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product_1.id,
                            "product_uom_qty": product_uom_qty,
                        }
                    ),
                ],
            }
        )

    @freezegun.freeze_time("2025-02-01")
    def test_delivery_line_moved_to_blanket_order_on_confirm(self):
        # All the invoicing must be done on the blanket order: the delivery
        # cost line computed for a call-off order must not stay on that
        # call-off order once it is confirmed.
        order = self._create_call_off_order(
            5.0, self.carrier_call_off_1.id, "2025-02-10 10:00:00"
        )
        order.set_delivery_line(self.carrier_call_off_1, 42.0)
        # Before confirmation, the delivery line stays on the call-off order.
        self.assertTrue(order.order_line.filtered("is_delivery"))
        self.assertFalse(self.blanket_so.order_line.filtered("is_delivery"))

        order.action_confirm()

        self.assertFalse(order.order_line.filtered("is_delivery"))
        blanket_delivery_lines = self.blanket_so.order_line.filtered("is_delivery")
        self.assertEqual(len(blanket_delivery_lines), 1)
        self.assertEqual(blanket_delivery_lines.price_unit, 42.0)
        # The carrier itself remains the one of the call-off order.
        self.assertEqual(order.carrier_id, self.carrier_call_off_1)

    @freezegun.freeze_time("2025-02-01")
    def test_delivery_line_not_moved_when_call_off_canceled_before_confirm(self):
        # Canceling a call-off order before it is confirmed must not leave
        # a stray delivery line on the blanket order.
        order = self._create_call_off_order(
            5.0, self.carrier_call_off_1.id, "2025-02-10 10:00:00"
        )
        order.set_delivery_line(self.carrier_call_off_1, 42.0)
        order.action_cancel()

        self.assertFalse(self.blanket_so.order_line.filtered("is_delivery"))

    @freezegun.freeze_time("2025-02-01")
    def test_call_off_orders_with_different_carrier_are_not_consolidated(self):
        # sale_order_blanket_order consolidates call-off orders sharing the
        # same commitment date into a single delivery. Here, both call-off
        # orders share the same commitment date but use a different delivery
        # method: they must not end up sharing the same delivery, since a
        # single delivery can only use a single carrier.
        commitment_date = "2025-02-10 10:00:00"
        order_1 = self._create_call_off_order(
            5.0, self.carrier_call_off_1.id, commitment_date
        )
        order_1.action_confirm()
        order_2 = self._create_call_off_order(
            5.0, self.carrier_call_off_2.id, commitment_date
        )
        order_2.action_confirm()

        picking_1 = order_1.order_line.blanket_move_ids.picking_id
        picking_2 = order_2.order_line.blanket_move_ids.picking_id

        self.assertTrue(picking_1)
        self.assertTrue(picking_2)
        self.assertNotEqual(picking_1, picking_2)
        self.assertEqual(picking_1.carrier_id, self.carrier_call_off_1)
        self.assertEqual(picking_2.carrier_id, self.carrier_call_off_2)

    @freezegun.freeze_time("2025-02-01")
    def test_call_off_orders_with_same_carrier_are_still_consolidated(self):
        # Call-off orders sharing both the same commitment date and the same
        # delivery method are still consolidated into a single delivery: the
        # carrier check must not defeat the consolidation implemented in
        # sale_order_blanket_order.
        commitment_date = "2025-02-10 10:00:00"
        order_1 = self._create_call_off_order(
            5.0, self.carrier_call_off_1.id, commitment_date
        )
        order_1.action_confirm()
        order_2 = self._create_call_off_order(
            5.0, self.carrier_call_off_1.id, commitment_date
        )
        order_2.action_confirm()

        picking_1 = order_1.order_line.blanket_move_ids.picking_id
        picking_2 = order_2.order_line.blanket_move_ids.picking_id

        self.assertTrue(picking_1)
        self.assertEqual(picking_1, picking_2)
        self.assertEqual(picking_1.carrier_id, self.carrier_call_off_1)
