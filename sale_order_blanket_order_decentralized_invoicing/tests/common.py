# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime, time, timedelta

from odoo import Command, fields

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


class DecentralizedInvoicingCommon(AccountTestInvoicingCommon):
    """Blanket order invoicing its call-offs at their own addresses."""

    @classmethod
    def get_default_groups(cls):
        # Same as sale's TestSaleCommon: the test user also sells.
        return super().get_default_groups() | cls.quick_ref(
            "sales_team.group_sale_manager"
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(cls.env.context, tracking_disable=True, no_reset_password=True)
        )
        # Done by the registry hook of sale_order_blanket_order, which doesn't
        # run in tests: keeps the price of confirmed blanket lines.
        cls.env["sale.order.line"]._do_patch_compute_price_unit()
        cls.env.company.blanket_invoice_call_off_at_own_address = True

        cls.customer = cls.env["res.partner"].create(
            {"name": "ACME", "is_company": True}
        )
        cls.address_paris = cls._create_address("ACME Paris", "delivery")
        cls.address_chambery = cls._create_address("ACME Chambéry", "delivery")
        cls.invoice_address_paris = cls._create_address(
            "ACME Accounting Paris", "invoice"
        )

        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.company.id)], limit=1
        )
        cls.product = cls._create_storable_product("Desk")

        today = fields.Date.today()
        # A fixed time of day, so a few hours later is still the same day
        cls.delivery_date = datetime.combine(today + timedelta(days=10), time(8, 0))
        cls.blanket = cls._create_blanket(
            cls.product,
            start_date=today,
            end_date=today + timedelta(days=90),
        )
        cls.blanket_line = cls.blanket.order_line

    @classmethod
    def _create_address(cls, name, address_type):
        return cls.env["res.partner"].create(
            {"name": name, "type": address_type, "parent_id": cls.customer.id}
        )

    @classmethod
    def _create_storable_product(cls, name):
        product = cls.env["product.product"].create(
            {
                "name": name,
                "is_storable": True,
                "invoice_policy": "delivery",
                "list_price": 100.0,
            }
        )
        cls.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "product_id": product.id,
                "inventory_quantity": 100.0,
                "location_id": cls.warehouse.lot_stock_id.id,
            }
        ).action_apply_inventory()
        return product

    @classmethod
    def _create_blanket(cls, product, start_date, end_date):
        """Create and confirm a blanket order of 10 units at the customer's address."""
        blanket = cls.env["sale.order"].create(
            {
                "order_type": "blanket",
                "partner_id": cls.customer.id,
                "partner_invoice_id": cls.customer.id,
                "partner_shipping_id": cls.customer.id,
                "blanket_validity_start_date": start_date,
                "blanket_validity_end_date": end_date,
                "blanket_reservation_strategy": "at_call_off",
                "order_line": [
                    Command.create(
                        {
                            "product_id": product.id,
                            "product_uom_qty": 10.0,
                            "price_unit": 100.0,
                        }
                    )
                ],
            }
        )
        blanket.action_confirm()
        return blanket

    @classmethod
    def _create_call_off(cls, qty, shipping=None, invoice=None, commitment_date=None):
        """Create and confirm a call-off, at the blanket order's addresses by default.

        The addresses are always given: the customer has delivery addresses,
        so the standard defaults would not be the blanket order's ones.
        """
        call_off = cls.env["sale.order"].create(
            {
                "order_type": "call_off",
                "partner_id": cls.customer.id,
                "partner_invoice_id": (invoice or cls.blanket.partner_invoice_id).id,
                "partner_shipping_id": (shipping or cls.blanket.partner_shipping_id).id,
                "blanket_order_id": cls.blanket.id,
                "commitment_date": commitment_date or cls.delivery_date,
                "order_line": [
                    Command.create(
                        {
                            "product_id": cls.blanket.order_line.product_id.id,
                            "product_uom_qty": qty,
                        }
                    )
                ],
            }
        )
        call_off.action_confirm()
        return call_off

    def _deliver(self, call_off, qty=None):
        """Deliver a call-off, all of it or a quantity with a backorder for the rest."""
        moves = call_off.order_line.blanket_move_ids.filtered(
            lambda move: move.state not in ("done", "cancel")
        )
        moves._action_assign()
        if qty is not None:
            moves.quantity = qty
        moves.picked = True
        moves._action_done()
        return moves

    def _return(self, call_off, qty):
        """Return a quantity delivered for a call-off, to be refunded."""
        delivery = call_off.order_line.blanket_move_ids.filtered(
            lambda move: move.state == "done"
        )
        picking = delivery.picking_id
        wizard = (
            self.env["stock.return.picking"]
            .with_context(
                active_id=picking.id,
                active_ids=picking.ids,
                active_model="stock.picking",
            )
            .create({})
        )
        for return_line in wizard.product_return_moves:
            return_line.quantity = qty if return_line.move_id in delivery else 0.0
        return_picking = wizard._create_return()
        return_picking.move_ids._action_assign()
        return_picking.move_ids.picked = True
        return_picking.move_ids._action_done()
        return return_picking
