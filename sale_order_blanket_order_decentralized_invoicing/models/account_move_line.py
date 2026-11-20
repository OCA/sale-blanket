# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # Set on the invoice lines of a blanket order line that invoice the delivered
    # quantity of a call-off invoiced at its own addresses. Empty on the lines
    # invoiced at the blanket order's addresses.
    call_off_sale_line_id = fields.Many2one(
        comodel_name="sale.order.line",
        string="Call-off Order Line",
        help="Call-off order line whose delivered quantity is invoiced by this "
        "line of the blanket order.",
        readonly=True,
        copy=False,
        index="btree_not_null",
    )

    def _copy_data_extend_business_fields(self, values):  # pylint: disable=missing-return
        # OVERRIDE: a credit note refunds the quantity of the same call-off, so
        # it can be invoiced again.
        super()._copy_data_extend_business_fields(values)
        values["call_off_sale_line_id"] = self.call_off_sale_line_id.id
