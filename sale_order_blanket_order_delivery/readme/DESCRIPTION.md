This module extends the Sale Order Blanket Order module to manage the
delivery of blanket orders.

The blanket order defines a default delivery method (carrier), applied to
every call-off order created from it. A "Strict Delivery Method" option lets
you enforce this default on all call-off orders, or leave it as a simple
default that can be overridden per call-off order.

Each call-off order can therefore be delivered with its own delivery method.
Call-off orders sharing the same requested delivery date and the same
delivery method are still grouped into a single delivery. All the invoicing,
including delivery costs, stays on the blanket order.
