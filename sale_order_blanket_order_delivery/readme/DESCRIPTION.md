# Sale Order Blanket Order — Delivery Compatibility

Glue module reconciling
[`sale_order_blanket_order`](https://github.com/OCA/sale-blanket) and
[`delivery`](https://github.com/odoo/odoo/tree/18.0/addons/delivery).

## Problem

When both modules are installed, blanket orders and
call-off orders can have delivery-fee line. Without
this module, when we add delivery fees, we have 2 issues:

### Bug during Call-off / Blanket order matching

The delivery-fee line participates in the blanket-order call-off
matching algorithm: each call-off's delivery line "consumes" capacity from
the blanket order's delivery line. After the first call-off, the blanket's
delivery line has zero remaining capacity, so the second call-off fails
confirmation with:

> The product is not part of linked blanket order

### Uninvoiced delivery fees


Delivery fees should be on the Call-offs since we cannot predict them on the blanket order.
But the lines are invoiced from the blanket order.

## What this module does

todo

