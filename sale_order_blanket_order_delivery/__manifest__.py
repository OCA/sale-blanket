# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Sale Order Blanket Order Delivery",
    "summary": """Manage deliveries of your blanket order""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/sale-blanket",
    "maintainers": ["lmignon"],
    "depends": [
        "sale_order_blanket_order",
        "delivery_procurement_group_carrier",
    ],
    "data": [
        "views/sale_order.xml",
    ],
    "demo": [],
}
