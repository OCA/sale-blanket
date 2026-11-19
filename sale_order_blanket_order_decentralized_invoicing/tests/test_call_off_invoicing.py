# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import DecentralizedInvoicingCommon


@tagged("post_install", "-at_install")
class TestCallOffInvoicing(DecentralizedInvoicingCommon):
    """Invoices of a blanket order split per addresses of its call-offs."""

    def _invoice_at(self, invoices, invoice_address, shipping_address):
        """Return the invoice of the given addresses among some invoices."""
        invoice = invoices.filtered(
            lambda move: (
                move.partner_id == invoice_address
                and move.partner_shipping_id == shipping_address
            )
        )
        self.assertEqual(len(invoice), 1)
        return invoice

    def test_00_same_address_invoice_unchanged(self):
        """Test call-offs at the blanket order's addresses are invoiced as before.

        The invoice line keeps its call-off without naming it.
        """
        call_off = self._create_call_off(3)
        self._deliver(call_off)
        invoices = self.blanket._create_invoices()
        invoice = self._invoice_at(invoices, self.customer, self.customer)
        self.assertEqual(invoices, invoice)
        self.assertRecordValues(
            invoice.invoice_line_ids,
            [{"quantity": 3.0, "call_off_sale_line_id": call_off.order_line.id}],
        )
        self.assertNotIn(call_off.name, invoice.invoice_line_ids.name)

    def test_01_invoice_per_call_off_addresses(self):
        """Test each call-off is invoiced at its own invoice and shipping addresses."""
        same_address = self._create_call_off(2)
        paris = self._create_call_off(
            3, shipping=self.address_paris, invoice=self.invoice_address_paris
        )
        self._deliver(same_address)
        self._deliver(paris)

        invoices = self.blanket._create_invoices()

        self.assertEqual(len(invoices), 2)
        blanket_invoice = self._invoice_at(invoices, self.customer, self.customer)
        self.assertRecordValues(
            blanket_invoice.invoice_line_ids,
            [{"quantity": 2.0, "call_off_sale_line_id": same_address.order_line.id}],
        )
        paris_invoice = self._invoice_at(
            invoices, self.invoice_address_paris, self.address_paris
        )
        self.assertRecordValues(
            paris_invoice.invoice_line_ids,
            [
                {
                    "quantity": 3.0,
                    "call_off_sale_line_id": paris.order_line.id,
                    "sale_line_ids": self.blanket_line.ids,
                }
            ],
        )
        self.assertIn(paris.name, paris_invoice.invoice_line_ids.name)
        self.assertEqual(self.blanket_line.qty_invoiced, 5.0)

    def test_02_same_addresses_grouped_on_one_invoice(self):
        """Test call-offs with the same addresses are invoiced together.

        They are delivered on different days, but they share their invoice,
        with a line per call-off.
        """
        first = self._create_call_off(
            3, shipping=self.address_paris, invoice=self.invoice_address_paris
        )
        second = self._create_call_off(
            2,
            shipping=self.address_paris,
            invoice=self.invoice_address_paris,
            commitment_date=self.delivery_date + timedelta(days=2),
        )
        self._deliver(first)
        self._deliver(second)

        invoices = self.blanket._create_invoices()

        invoice = self._invoice_at(
            invoices, self.invoice_address_paris, self.address_paris
        )
        self.assertEqual(invoices, invoice)
        self.assertRecordValues(
            invoice.invoice_line_ids.sorted("quantity"),
            [
                {"quantity": 2.0, "call_off_sale_line_id": second.order_line.id},
                {"quantity": 3.0, "call_off_sale_line_id": first.order_line.id},
            ],
        )

    def test_03_delivered_qty_invoiced_once(self):
        """Test a delivered quantity of a call-off is invoiced only once.

        The next invoicing only takes the new deliveries of the same addresses,
        and fails when nothing new is delivered.
        """
        first = self._create_call_off(3, shipping=self.address_paris)
        self._deliver(first)
        self.blanket._create_invoices().action_post()

        second = self._create_call_off(
            2,
            shipping=self.address_paris,
            commitment_date=self.delivery_date + timedelta(days=2),
        )
        self._deliver(second)
        invoice = self.blanket._create_invoices()
        self.assertRecordValues(
            invoice.invoice_line_ids,
            [{"quantity": 2.0, "call_off_sale_line_id": second.order_line.id}],
        )
        invoice.action_post()
        self.assertEqual(self.blanket_line.qty_to_invoice, 0.0)

        with self.assertRaisesRegex(UserError, "No items are available to invoice"):
            self.blanket._create_invoices()

    def test_04_return_gives_credit_note_at_call_off_addresses(self):
        """Test a return of a call-off is refunded at the call-off's addresses."""
        paris = self._create_call_off(
            3, shipping=self.address_paris, invoice=self.invoice_address_paris
        )
        self._deliver(paris)
        self.blanket._create_invoices().action_post()
        self._return(paris, 1.0)

        credit_note = self.blanket._create_invoices(final=True)

        self.assertRecordValues(
            credit_note,
            [
                {
                    "move_type": "out_refund",
                    "partner_id": self.invoice_address_paris.id,
                    "partner_shipping_id": self.address_paris.id,
                }
            ],
        )
        self.assertRecordValues(
            credit_note.invoice_line_ids,
            [{"quantity": 1.0, "call_off_sale_line_id": paris.order_line.id}],
        )
        self.assertEqual(self.blanket_line.qty_invoiced, 2.0)

    def test_05_reversed_invoice_can_be_invoiced_again(self):
        """Test the credit note of a call-off invoice gives its quantity back.

        The reversal keeps the call-off of each line, so the quantity is
        invoiced again at the call-off's addresses.
        """
        paris = self._create_call_off(3, shipping=self.address_paris)
        self._deliver(paris)
        invoice = self.blanket._create_invoices()
        invoice.action_post()
        credit_note = invoice._reverse_moves(cancel=True)
        self.assertEqual(
            credit_note.invoice_line_ids.call_off_sale_line_id, paris.order_line
        )

        new_invoice = self.blanket._create_invoices()

        self._invoice_at(new_invoice, self.customer, self.address_paris)
        self.assertRecordValues(
            new_invoice.invoice_line_ids,
            [{"quantity": 3.0, "call_off_sale_line_id": paris.order_line.id}],
        )

    def test_06_address_change_after_invoice_keeps_invoice(self):
        """Test a new invoice address of a call-off only applies to next invoices."""
        paris = self._create_call_off(
            5, shipping=self.address_paris, invoice=self.invoice_address_paris
        )
        self._deliver(paris, qty=3.0)
        invoice = self.blanket._create_invoices()

        paris.partner_invoice_id = self.address_chambery
        self._deliver(paris)
        new_invoice = self.blanket._create_invoices()

        self.assertEqual(invoice.partner_id, self.invoice_address_paris)
        self.assertEqual(invoice.invoice_line_ids.quantity, 3.0)
        self._invoice_at(new_invoice, self.address_chambery, self.address_paris)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 2.0)

    def test_07_invoice_wizard_without_consolidation(self):
        """Test the invoicing wizard splits per addresses, not consolidated."""
        same_address = self._create_call_off(2)
        paris = self._create_call_off(3, shipping=self.address_paris)
        self._deliver(same_address)
        self._deliver(paris)
        wizard = (
            self.env["sale.advance.payment.inv"]
            .with_context(active_model="sale.order", active_ids=self.blanket.ids)
            .create(
                {"advance_payment_method": "delivered", "consolidated_billing": False}
            )
        )

        wizard.create_invoices()

        invoices = self.blanket.invoice_ids
        self.assertEqual(len(invoices), 2)
        self._invoice_at(invoices, self.customer, self.customer)
        self._invoice_at(invoices, self.customer, self.address_paris)

    def test_08_option_off_invoices_at_blanket_addresses(self):
        """Test a blanket order without the option invoices at its own addresses.

        The deliveries of a call-off with other addresses are invoiced with
        the rest of the blanket order.
        """
        self.blanket.invoice_call_off_at_own_address = False
        paris = self._create_call_off(
            3, shipping=self.address_paris, invoice=self.invoice_address_paris
        )
        self._deliver(paris)

        invoices = self.blanket._create_invoices()

        invoice = self._invoice_at(invoices, self.customer, self.customer)
        self.assertEqual(invoices, invoice)
        self.assertRecordValues(
            invoice.invoice_line_ids,
            [{"quantity": 3.0, "call_off_sale_line_id": False}],
        )

    def test_09_company_setting_is_the_blanket_default(self):
        """Test new blanket orders take the option from the company setting."""
        self.assertTrue(self.blanket.invoice_call_off_at_own_address)
        self.env["res.config.settings"].create(
            {"blanket_invoice_call_off_at_own_address": False}
        ).execute()

        today = fields.Date.today()
        blanket = self.env["sale.order"].create(
            {
                "order_type": "blanket",
                "partner_id": self.customer.id,
                "blanket_validity_start_date": today,
                "blanket_validity_end_date": today + timedelta(days=90),
            }
        )

        self.assertFalse(self.env.company.blanket_invoice_call_off_at_own_address)
        self.assertFalse(blanket.invoice_call_off_at_own_address)
        self.assertTrue(self.blanket.invoice_call_off_at_own_address)

    def test_10_call_off_moved_after_invoice_not_invoiced_again(self):
        """Test a call-off invoiced at the blanket order's addresses, then moved.

        Its invoice line keeps the call-off, so the quantity already invoiced
        isn't invoiced again at the new address, and the next deliveries at
        the blanket order's addresses are invoiced there.
        """
        first = self._create_call_off(3)
        self._deliver(first)
        self.blanket._create_invoices().action_post()

        first.partner_shipping_id = self.address_paris
        second = self._create_call_off(2)
        self._deliver(second)
        invoices = self.blanket._create_invoices()

        invoice = self._invoice_at(invoices, self.customer, self.customer)
        self.assertEqual(invoices, invoice)
        self.assertRecordValues(
            invoice.invoice_line_ids,
            [{"quantity": 2.0, "call_off_sale_line_id": second.order_line.id}],
        )
        self.assertEqual(self.blanket_line.qty_invoiced, 5.0)

    def test_11_option_enabled_after_invoice_not_invoiced_again(self):
        """Test the quantities invoiced before the option is enabled stay invoiced.

        Their invoice lines have no call-off: they are deducted from the oldest
        call-offs, so only the new deliveries are invoiced, at their call-off's
        addresses.
        """
        self.blanket.invoice_call_off_at_own_address = False
        paris = self._create_call_off(3, shipping=self.address_paris)
        self._deliver(paris)
        self.blanket._create_invoices().action_post()

        self.blanket.invoice_call_off_at_own_address = True
        chambery = self._create_call_off(2, shipping=self.address_chambery)
        self._deliver(chambery)
        invoices = self.blanket._create_invoices()

        invoice = self._invoice_at(invoices, self.customer, self.address_chambery)
        self.assertEqual(invoices, invoice)
        self.assertRecordValues(
            invoice.invoice_line_ids,
            [{"quantity": 2.0, "call_off_sale_line_id": chambery.order_line.id}],
        )
        self.assertEqual(self.blanket_line.qty_invoiced, 5.0)
