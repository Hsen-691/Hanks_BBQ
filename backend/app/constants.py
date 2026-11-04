"""Shared constants."""

# The order lifecycle, matching the admin board and the customer tracker.
ORDER_STATUSES = [
    "pending",
    "preparing",
    "ready",
    "out_for_delivery",
    "delivered",
    "cancelled",
]
