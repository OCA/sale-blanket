# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.sale_order_blanket_order.tests.common import SaleOrderBlanketOrderCase


class SaleOrderBlanketOrderDeliveryCase(SaleOrderBlanketOrderCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        delivery_product = cls.env.ref("delivery.product_product_delivery")
        cls.carrier_blanket = cls.env["delivery.carrier"].create(
            {
                "name": "Carrier Blanket",
                "product_id": delivery_product.id,
            }
        )
        cls.carrier_call_off_1 = cls.env["delivery.carrier"].create(
            {
                "name": "Carrier Call-off 1",
                "product_id": delivery_product.id,
            }
        )
        cls.carrier_call_off_2 = cls.env["delivery.carrier"].create(
            {
                "name": "Carrier Call-off 2",
                "product_id": delivery_product.id,
            }
        )
