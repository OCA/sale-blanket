A blanket order of 100 desks for ACME, shipped and invoiced to ACME, has the
option enabled:

1. Call-off 1: 5 desks for ACME.
2. Call-off 2: 5 desks shipped to ACME Chambéry.
3. Call-off 3: 5 desks shipped to ACME Chambéry on another day.
4. Call-off 4: 5 desks shipped to ACME Paris and invoiced to ACME Accounting
   Paris.

Once everything is delivered, creating the invoices of the blanket order gives
three invoices:

- 5 desks invoiced to ACME;
- 10 desks invoiced to ACME and shipped to ACME Chambéry, with a line per
  call-off order;
- 5 desks invoiced to ACME Accounting Paris and shipped to ACME Paris.

Every invoice line keeps its call-off order line, also at the addresses of the
blanket order, where the call-off order isn't named on the line:

- a delivered quantity is invoiced only once;
- the returns of a call-off order are refunded at its addresses;
- a credit note gives the quantity back to the call-off order, to be
  invoiced again;
- changing the addresses of a call-off order doesn't change its existing
  invoices, the next quantities are invoiced at the new addresses.

When the option is enabled on a blanket order already invoiced, its existing
invoice lines have no call-off order: their quantity is deducted from its
oldest call-off orders, so it isn't invoiced again.

Products invoiced on ordered quantities are always invoiced at the addresses
of the blanket order.
