# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Sale Blanket Order Decentralized Invoicing",
    "summary": "Invoice call-off orders at their own addresses",
    "version": "19.0.1.0.0",
    "license": "AGPL-3",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/sale-blanket",
    "depends": [
        "sale_order_blanket_order",
    ],
    "data": [
        "views/res_config_settings.xml",
        "views/sale_order.xml",
    ],
}
