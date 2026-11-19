With `sale_order_blanket_order`, the deliveries of call-off orders are invoiced
through their blanket order, at the invoice and shipping addresses of the
blanket order.

This module adds an option to blanket orders to invoice the deliveries of a
call-off order at the invoice and shipping addresses of the call-off order,
when they differ from the blanket order's ones. The invoices are still created
from the blanket order: one invoice per invoice and shipping addresses, with a
line per call-off order.
