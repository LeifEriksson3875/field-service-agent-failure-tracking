"""Track a photo review and technician follow-up as one observable workflow."""
from dataclasses import dataclass
from typing import Any

from infrai_client import InfraiClient


@dataclass(frozen=True)
class WorkOrder:
    work_order_id: str
    photo_count: int
    dispatch_status: str
    technician_confirmed: bool


def next_action(order: WorkOrder) -> str:
    """Choose the next operational action from the work-order state."""
    if order.photo_count == 0:
        return "request_follow_up"
    if order.dispatch_status != "dispatched":
        return "hold_dispatch"
    if not order.technician_confirmed:
        return "await_technician"
    return "close_work_order"


def process_work_order(order: WorkOrder, client: InfraiClient) -> str:
    try:
        action = next_action(order)
        if action == "request_follow_up":
            raise ValueError("work-order photo is required before review")
        return action
    except Exception as exc:
        client.capture({
            "type": type(exc).__name__,
            "value": str(exc),
            "context": {
                "work_order_id": order.work_order_id,
                "photo_count": order.photo_count,
                "dispatch_status": order.dispatch_status,
                "technician_confirmed": order.technician_confirmed,
            },
        })
        return "request_follow_up"


if __name__ == "__main__":
    client = InfraiClient()
    order = WorkOrder("WO-1042", photo_count=0, dispatch_status="dispatched", technician_confirmed=False)
    print(process_work_order(order, client))
