# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import freezegun

from odoo import Command

from .common import SaleOrderBlanketOrderCase


class TestSaleCallOffOrderProcessing(SaleOrderBlanketOrderCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.blanket_so.action_confirm()

    @freezegun.freeze_time("2025-02-01")
    def test_no_reservation_processing(self):
        # Create a call-off order without reservation
        order = self.env["sale.order"].create(
            {
                "order_type": "call_off",
                "partner_id": self.partner.id,
                "blanket_order_id": self.blanket_so.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product_1.id,
                            "product_uom_qty": 10.0,
                        }
                    ),
                    Command.create(
                        {
                            "product_id": self.product_2.id,
                            "product_uom_qty": 10.0,
                        }
                    ),
                ],
            }
        )
        order.action_confirm()
        self.assertEqual(order.state, "sale")
        self.assertRecordValues(
            order.order_line,
            [
                {
                    "product_uom_qty": 10.0,
                    "price_unit": 0.0,
                    "qty_to_deliver": 0.0,
                    "qty_to_invoice": 0.0,
                    "qty_delivered": 0.0,
                    "display_qty_widget": False,
                },
                {
                    "product_uom_qty": 10.0,
                    "price_unit": 0.0,
                    "qty_to_deliver": 0.0,
                    "qty_to_invoice": 0.0,
                    "qty_delivered": 0.0,
                    "display_qty_widget": False,
                },
            ],
        )

        # The lines should be linked to moves linked to a blanked order line
        for line in order.order_line:
            self.assertTrue(line.blanket_move_ids)
            sale_line = line.blanket_move_ids.sale_line_id
            self.assertEqual(sale_line.product_id, line.product_id)
            self.assertEqual(sale_line.order_id, self.blanket_so)

        # process the picking
        picking = line.blanket_move_ids.picking_id
        picking.action_assign()
        picking.move_line_ids.picked = True
        picking._action_done()

        blanket_lines = self.blanket_so.order_line

        # part of the quantity into the blanket order are now delivered
        for product in [self.product_1, self.product_2]:
            self.assertEqual(
                sum(
                    blanket_lines.filtered(
                        lambda line, product=product: line.product_id == product
                    ).mapped("qty_delivered")
                ),
                10.0,
            )

    @freezegun.freeze_time("2025-02-01")
    def test_no_reservation_processing_2(self):
        # In this test we create a call-off order with 1 lines
        # for product 1 where the quantity to deliver is greater
        # than the quantity defined per line in the blanket order.
        # On the blanket order we have 2 lines for product 1 with
        # 10.0 quantity each.
        # The call-off order will have 1 line for product 1 with
        # 15.0 quantity.

        order = self.env["sale.order"].create(
            {
                "order_type": "call_off",
                "partner_id": self.partner.id,
                "blanket_order_id": self.blanket_so.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product_1.id,
                            "product_uom_qty": 15.0,
                        }
                    ),
                ],
            }
        )
        order.action_confirm()
        self.assertEqual(order.state, "sale")

        # process the picking
        picking = order.order_line.blanket_move_ids.picking_id
        picking.action_assign()
        picking.move_line_ids.picked = True
        picking._action_done()

        blanket_lines = self.blanket_so.order_line
        self.assertEqual(
            sum(
                blanket_lines.filtered(
                    lambda line: line.product_id == self.product_1
                ).mapped("qty_delivered")
            ),
            15.0,
        )

    @freezegun.freeze_time("2025-02-01")
    def test_full_call_off_no_empty_reservation_reference(self):
        order = self.env["sale.order"].create(
            {
                "order_type": "call_off",
                "partner_id": self.partner.id,
                "blanket_order_id": self.blanket_so.id,
                "order_line": [
                    Command.create(
                        {"product_id": self.product_1.id, "product_uom_qty": 20.0}
                    ),
                    Command.create(
                        {"product_id": self.product_2.id, "product_uom_qty": 10.0}
                    ),
                ],
            }
        )
        order.action_confirm()
        self.assertFalse(
            self.env["stock.reference"].search(
                [
                    ("name", "=", f"Reservation for {self.blanket_so.name}"),
                    ("move_ids", "=", False),
                ]
            )
        )

    def _get_reservation_moves(self, product):
        return self.blanket_so.order_line.move_ids.filtered(
            lambda m: m.used_for_sale_reservation
            and m.state != "cancel"
            and m.product_id == product
        )

    def _get_reserved_qty(self, product):
        moves = self._get_reservation_moves(product)
        return sum(moves.mapped("product_uom_qty"))

    def _create_call_off_order(self, product_uom_qty, partner_shipping):
        return self.env["sale.order"].create(
            {
                "order_type": "call_off",
                "partner_id": self.partner.id,
                "partner_shipping_id": partner_shipping.id,
                "blanket_order_id": self.blanket_so.id,
                "commitment_date": "2025-02-10 10:00:00",
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product_2.id,
                            "product_uom_qty": product_uom_qty,
                        }
                    ),
                ],
            }
        )

    @freezegun.freeze_time("2025-02-01")
    def test_call_off_order_delivered_at_own_address(self):
        """Test a call-off order is delivered at its own address.

        The quantity still to call off stays reserved at the address of the
        blanket order, in the reservation picking.
        """
        address = self._create_delivery_address("Warehouse")
        order = self._create_call_off_order(4.0, address)
        order.action_confirm()

        delivery_moves = order.order_line.blanket_move_ids
        self.assertEqual(sum(delivery_moves.mapped("product_uom_qty")), 4.0)
        self.assertEqual(delivery_moves.partner_id, address)
        self.assertEqual(delivery_moves.picking_id.partner_id, address)
        reservation_moves = self._get_reservation_moves(self.product_2)
        self.assertEqual(sum(reservation_moves.mapped("product_uom_qty")), 6.0)
        self.assertEqual(
            reservation_moves.partner_id, self.blanket_so.partner_shipping_id
        )
        self.assertNotEqual(reservation_moves.picking_id, delivery_moves.picking_id)

    @freezegun.freeze_time("2025-02-01")
    def test_call_off_orders_to_same_address_share_picking(self):
        """Test call-off orders to the same address and day share a picking.

        Canceling one of them keeps the picking of the other one and reserves
        its quantity again on the blanket order.
        """
        address = self._create_delivery_address("Warehouse")
        order_1 = self._create_call_off_order(4.0, address)
        order_1.action_confirm()
        order_2 = self._create_call_off_order(3.0, address)
        order_2.action_confirm()

        moves_1 = order_1.order_line.blanket_move_ids
        moves_2 = order_2.order_line.blanket_move_ids
        picking = moves_1.picking_id
        self.assertEqual(moves_2.picking_id, picking)
        self.assertEqual(picking.partner_id, address)
        self.assertEqual(self._get_reserved_qty(self.product_2), 3.0)

        order_1._action_cancel()

        self.assertEqual(set(moves_1.mapped("state")), {"cancel"})
        self.assertNotIn("cancel", moves_2.mapped("state"))
        self.assertEqual(moves_2.picking_id, picking)
        self.assertEqual(self._get_reserved_qty(self.product_2), 7.0)

    @freezegun.freeze_time("2025-02-01")
    def test_cancel_call_off_order(self):
        self.assertEqual(self._get_reserved_qty(self.product_2), 10.0)
        order = self.env["sale.order"].create(
            {
                "order_type": "call_off",
                "partner_id": self.partner.id,
                "blanket_order_id": self.blanket_so.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product_2.id,
                            "product_uom_qty": 4.0,
                        }
                    ),
                ],
            }
        )
        order.action_confirm()
        delivery_moves = order.order_line.blanket_move_ids
        self.assertFalse(any(delivery_moves.mapped("used_for_sale_reservation")))
        self.assertEqual(sum(delivery_moves.mapped("product_uom_qty")), 4.0)
        self.assertEqual(self._get_reserved_qty(self.product_2), 6.0)

        order._action_cancel()

        self.assertEqual(set(delivery_moves.mapped("state")), {"cancel"})
        # The qty no more called off is reserved again on the blanket order
        self.assertEqual(self._get_reserved_qty(self.product_2), 10.0)
        self.assertEqual(self._get_reserved_qty(self.product_1), 20.0)


class TestSaleAutoDoneCallOffOrderProcessing(TestSaleCallOffOrderProcessing):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids += cls.env.ref("sale.group_auto_done_setting")
