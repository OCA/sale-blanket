On a blanket order:

- Set the *Delivery Method* to define the default carrier used by its
  call-off orders.
- Check *Strict Delivery Method* to prevent call-off orders from using a
  different delivery method. Leave it unchecked to only use it as a default,
  freely overridable on each call-off order.

On a call-off order:

- The *Delivery Method* defaults from the blanket order and can be changed
  (unless *Strict Delivery Method* is enabled), before the call-off order is
  confirmed.
- Once confirmed, call-off orders sharing the same requested delivery date
  and the same delivery method are shipped together in a single delivery;
  others are shipped separately.
- Any delivery cost added on a call-off order is moved to the blanket order
  when the call-off order is confirmed, since all the invoicing is done on
  the blanket order. The delivery method itself cannot be changed anymore
  once the call-off order is confirmed.
