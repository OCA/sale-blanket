# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    invoice_call_off_at_own_address = fields.Boolean(
        string="Invoice Call-offs at their Addresses",
        default=lambda self: self.env.company.blanket_invoice_call_off_at_own_address,
        tracking=True,
        help="When checked, the delivered quantities of a call-off order with "
        "other invoice or shipping addresses than this blanket order are invoiced "
        "at the addresses of the call-off order. Otherwise, all the quantities are "
        "invoiced at the addresses of the blanket order.",
    )

    def _get_invoice_address_ids(self):
        """Return the addresses an order is invoiced at.

        :return: tuple (invoice partner id, shipping partner id)
        """
        self.ensure_one()
        return (self.partner_invoice_id.id, self.partner_shipping_id.id)

    def _is_invoiced_apart(self):
        """Tell whether a call-off order is invoiced apart from its blanket order.

        When its blanket order has the option enabled, a call-off with other
        invoice or shipping addresses than its blanket order has its deliveries
        invoiced at its own addresses. Otherwise, its deliveries are invoiced
        with the blanket order.

        :return: True for a call-off invoiced at its own addresses
        """
        self.ensure_one()
        return (
            self.order_type == "call_off"
            and self.blanket_order_id.invoice_call_off_at_own_address
            and self._get_invoice_address_ids()
            != self.blanket_order_id._get_invoice_address_ids()
        )

    def _get_call_off_invoice_address_groups(self, final=False):
        """Group the blanket orders to invoice per addresses of their call-offs.

        Only the blanket orders having a quantity to invoice for a call-off are
        returned, so that each invoice line keeps its call-off. Each of them is
        also grouped under its own addresses, for its call-offs at these
        addresses and the rest of its quantities.

        Example: a blanket order of ACME with a call-off invoiced in Paris returns
        ``{(ACME, ACME): blanket, (ACME Paris, ACME Paris): blanket}``.

        :param final: whether negative quantities are invoiced as credit notes
        :return: dict {(invoice partner id, shipping partner id): blanket orders}
        """
        groups = defaultdict(self.browse)
        for order in self.filtered(lambda order: order.order_type == "blanket"):
            addresses = set()
            for line in order.order_line:
                if line.display_type or line.is_downpayment:
                    continue
                for call_off_line, qty in line._get_call_off_invoice_split().items():
                    if line._is_call_off_qty_invoiceable(qty, final=final):
                        addresses.add(call_off_line.order_id._get_invoice_address_ids())
            if addresses:
                addresses.add(order._get_invoice_address_ids())
            for address_ids in addresses:
                groups[address_ids] |= order
        return groups

    def _create_invoices(self, grouped=False, final=False, date=None):
        # OVERRIDE: a blanket order invoicing its call-offs at their addresses
        # is invoiced once per addresses, each pass running the standard
        # invoicing on the quantities of these addresses. Quantities of the
        # same addresses still end up on the same invoice, also across blanket
        # orders.
        if self.env.context.get("call_off_invoice_addresses"):
            return super()._create_invoices(grouped=grouped, final=final, date=date)
        address_groups = self._get_call_off_invoice_address_groups(final=final)
        if not address_groups:
            return super()._create_invoices(grouped=grouped, final=final, date=date)
        split_orders = self.browse().union(*address_groups.values())
        moves = self.env["account.move"]
        other_orders = self - split_orders
        if other_orders:
            moves |= super(
                SaleOrder, other_orders.with_context(raise_if_nothing_to_invoice=False)
            )._create_invoices(grouped=grouped, final=final, date=date)
        for address_ids, orders in address_groups.items():
            orders = orders.with_context(
                raise_if_nothing_to_invoice=False,
                call_off_invoice_addresses=address_ids,
                call_off_invoice_final=final,
            )
            moves |= super(SaleOrder, orders)._create_invoices(
                grouped=grouped, final=final, date=date
            )
        if not moves and self.env.context.get("raise_if_nothing_to_invoice", True):
            raise UserError(self._nothing_to_invoice_error_message())
        return moves.with_env(self.env)

    def _prepare_invoice(self):
        # OVERRIDE: address the invoice of a blanket order to the call-off
        # addresses being invoiced.
        vals = super()._prepare_invoice()
        address_ids = self.env.context.get("call_off_invoice_addresses")
        if address_ids and self.order_type == "blanket":
            vals["partner_id"], vals["partner_shipping_id"] = address_ids
        return vals

    def _get_invoiceable_lines(self, final=False):
        # OVERRIDE: while a blanket order is invoiced at some addresses, keep
        # the lines with a quantity to invoice at these addresses. Down payments
        # stay with the blanket order's own addresses.
        lines = super()._get_invoiceable_lines(final=final)
        address_ids = self.env.context.get("call_off_invoice_addresses")
        if not address_ids or self.order_type != "blanket":
            return lines
        own_addresses = address_ids == self._get_invoice_address_ids()
        return lines.filtered(
            lambda line: (
                line.display_type
                or (line.is_downpayment and own_addresses)
                or (
                    not line.is_downpayment
                    and line._get_call_off_invoice_quantities(address_ids, final=final)
                )
            )
        )
