- The delivery method of a call-off order cannot be changed once it is
  confirmed (its delivery is already being prepared against the blanket
  order). Changing it would require unwinding and relaunching that
  preparation, which is not supported.

- Support a "global" delivery cost scope for a blanket order, where a single
  forfeited delivery cost is agreed for the whole blanket order (as opposed
  to the "per call-off" scope currently implemented, where each call-off
  order defines its own delivery method and cost). This requires deciding how
  the global cost is allocated: invoiced on a single (e.g. first or last)
  call-off order, prorated across call-off orders, or invoiced separately
  from the call-off orders altogether.
