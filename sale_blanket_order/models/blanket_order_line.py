# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from odoo.tools.misc import format_date


class BlanketOrderLine(models.Model):
    _name = "sale.blanket.order.line"
    _description = "Blanket Order Line"
    _inherit = ["mail.thread", "mail.activity.mixin", "analytic.mixin"]

    @api.depends(
        "original_uom_qty",
        "price_unit",
        "taxes_id",
        "order_id.partner_id",
        "product_id",
        "currency_id",
    )
    def _compute_amount(self):
        for line in self:
            price = line.price_unit
            taxes = line.taxes_id.compute_all(
                price,
                line.currency_id,
                line.original_uom_qty,
                product=line.product_id,
                partner=line.order_id.partner_id,
            )
            line.update(
                {
                    "price_tax": sum(
                        t.get("amount", 0.0) for t in taxes.get("taxes", [])
                    ),
                    "price_total": taxes["total_included"],
                    "price_subtotal": taxes["total_excluded"],
                }
            )

    name = fields.Char("Description", tracking=True)
    sequence = fields.Integer()
    order_id = fields.Many2one("sale.blanket.order", required=True, ondelete="cascade")
    product_id = fields.Many2one(
        "product.product",
        string="Product",
        domain=[("sale_ok", "=", True)],
    )
    product_uom = fields.Many2one("uom.uom", string="Unit of Measure")
    price_unit = fields.Float(string="Price", digits="Product Price")
    taxes_id = fields.Many2many(
        comodel_name="account.tax",
        context={"active_test": False},
        check_company=True,
    )
    date_schedule = fields.Date(string="Scheduled Date")
    original_uom_qty = fields.Float(
        string="Original quantity", default=1, digits="Product Unit of Measure"
    )
    ordered_uom_qty = fields.Float(
        string="Ordered quantity", compute="_compute_quantities", store=True
    )
    invoiced_uom_qty = fields.Float(
        string="Invoiced quantity", compute="_compute_quantities", store=True
    )
    remaining_uom_qty = fields.Float(
        string="Remaining quantity", compute="_compute_quantities", store=True
    )
    remaining_qty = fields.Float(
        string="Remaining quantity in base UoM",
        compute="_compute_quantities",
        store=True,
    )
    delivered_uom_qty = fields.Float(
        string="Delivered quantity", compute="_compute_quantities", store=True
    )
    sale_lines = fields.One2many(
        "sale.order.line",
        "blanket_order_line",
        string="Sale order lines",
        readonly=True,
        copy=False,
    )
    company_id = fields.Many2one(
        related="order_id.company_id", store=True, index=True, precompute=True
    )
    currency_id = fields.Many2one("res.currency", related="order_id.currency_id")
    partner_id = fields.Many2one(related="order_id.partner_id", string="Customer")
    user_id = fields.Many2one(related="order_id.user_id", string="Responsible")
    payment_term_id = fields.Many2one(
        related="order_id.payment_term_id", string="Payment Terms"
    )
    pricelist_id = fields.Many2one(related="order_id.pricelist_id", string="Pricelist")

    price_subtotal = fields.Monetary(
        compute="_compute_amount", string="Subtotal", store=True
    )
    price_total = fields.Monetary(compute="_compute_amount", string="Total", store=True)
    price_tax = fields.Float(compute="_compute_amount", string="Tax", store=True)
    display_type = fields.Selection(
        [("line_section", "Section"), ("line_note", "Note")],
        default=False,
        help="Technical field for UX purpose.",
    )
    pricelist_item_id = fields.Many2one(
        comodel_name="product.pricelist.item", compute="_compute_pricelist_item_id"
    )

    @api.depends(
        "order_id.name", "date_schedule", "remaining_uom_qty", "product_uom.name"
    )
    @api.depends_context("from_sale_order")
    def _compute_display_name(self):
        if self.env.context.get("from_sale_order"):
            for record in self:
                name = f"[{record.order_id.name}]"
                if record.date_schedule:
                    formatted_date = format_date(record.env, record.date_schedule)
                    name += " - {}: {}".format(
                        self.env._("Date Scheduled"), formatted_date
                    )
                name += " ({}: {} {})".format(
                    self.env._("remaining"),
                    record.remaining_uom_qty,
                    record.product_uom.name,
                )
                record.display_name = name
        else:
            return super()._compute_display_name()

    def _get_display_price(self):
        # Copied and adapted from the sale module
        # No need to call _get_pricelist_price_before_discount()
        # since BO lines cannot have discounts
        # TODO: handle combos the way Odoo does in the sale module
        self.ensure_one()
        pricelist_price = self._get_pricelist_price()
        return pricelist_price

    def _get_pricelist_price(self):
        # Copied and adapted from the sale module
        self.ensure_one()
        self.product_id.ensure_one()
        price = self.pricelist_item_id._compute_price(
            product=self.product_id,
            quantity=self.original_uom_qty or 1.0,
            uom=self.product_uom,
            date=fields.Date.today(),
            currency=self.currency_id,
        )
        return price

    @api.onchange("product_id", "original_uom_qty")
    def onchange_product(self):
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        if self.product_id:
            name = self.product_id.name
            if not self.product_uom:
                self.product_uom = self.product_id.uom_id.id
            if self.order_id.partner_id and float_is_zero(
                self.price_unit, precision_digits=precision
            ):
                self.price_unit = self._get_display_price()
            if self.product_id.code:
                name = f"[{name}] {self.product_id.code}"
            if self.product_id.description_sale:
                name += "\n" + self.product_id.description_sale
            self.name = name

            fpos = self.order_id.fiscal_position_id
            self.taxes_id = fpos.map_tax(
                self.product_id.taxes_id._filter_taxes_by_company(self.company_id)
            )

    @api.depends(
        "sale_lines.order_id.state",
        "sale_lines.blanket_order_line",
        "sale_lines.product_uom_qty",
        "sale_lines.product_uom",
        "sale_lines.qty_delivered",
        "sale_lines.qty_invoiced",
        "original_uom_qty",
        "product_uom",
    )
    def _compute_quantities(self):
        for line in self:
            sale_lines = line.sale_lines
            line.ordered_uom_qty = sum(
                sl.product_uom._compute_quantity(sl.product_uom_qty, line.product_uom)
                for sl in sale_lines
                if sl.order_id.state != "cancel" and sl.product_id == line.product_id
            )
            line.invoiced_uom_qty = sum(
                sl.product_uom._compute_quantity(sl.qty_invoiced, line.product_uom)
                for sl in sale_lines
                if sl.order_id.state != "cancel" and sl.product_id == line.product_id
            )
            line.delivered_uom_qty = sum(
                sl.product_uom._compute_quantity(sl.qty_delivered, line.product_uom)
                for sl in sale_lines
                if sl.order_id.state != "cancel" and sl.product_id == line.product_id
            )
            line.remaining_uom_qty = line.original_uom_qty - line.ordered_uom_qty
            line.remaining_qty = line.product_uom._compute_quantity(
                line.remaining_uom_qty, line.product_id.uom_id
            )

    @api.depends("product_id", "product_uom", "original_uom_qty")
    def _compute_pricelist_item_id(self):
        # Copied and adapted from the sale module
        for line in self:
            if (
                not line.product_id
                or line.display_type
                or not line.order_id.pricelist_id
            ):
                line.pricelist_item_id = False
            else:
                line.pricelist_item_id = line.order_id.pricelist_id._get_product_rule(
                    line.product_id,
                    quantity=line.original_uom_qty or 1.0,
                    uom=line.product_uom,
                    date=fields.Date.today(),
                )

    def _validate(self):
        try:
            for line in self:
                assert (
                    not line.display_type and line.original_uom_qty > 0.0
                ) or line.display_type, self.env._("Quantity must be greater than zero")
        except AssertionError as e:
            raise UserError(e) from e

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if values.get(
                "display_type", self.default_get(["display_type"])["display_type"]
            ):
                values.update(product_id=False, price_unit=0, product_uom=False)

        return super().create(vals_list)

    _sql_constraints = [
        (
            "accountable_required_fields",
            """
            CHECK(
                display_type IS NOT NULL OR (
                    product_id IS NOT NULL AND product_uom IS NOT NULL
                    )
            )
            """,
            "Missing required fields on accountable sale order line.",
        ),
        (
            "non_accountable_null_fields",
            """
            CHECK(
                display_type IS NULL OR (
                    product_id IS NULL AND price_unit = 0 AND product_uom IS NULL
                    )
            )
            """,
            "Forbidden values on non-accountable sale order line",
        ),
    ]

    def write(self, values):
        if "display_type" in values and self.filtered(
            lambda line: line.display_type != values.get("display_type")
        ):
            raise UserError(
                self.env._(
                    """
                    You cannot change the type of a sale order line.
                    Instead you should delete the current line and create a new line
                    of the proper type.
                    """
                )
            )
        return super().write(values)
