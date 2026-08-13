import unittest

from field_service_agent import WorkOrder, next_action


class WorkOrderDecisionTest(unittest.TestCase):
    def test_missing_photo_requires_technician_follow_up(self) -> None:
        order = WorkOrder("WO-1042", 0, "dispatched", False)
        self.assertEqual(next_action(order), "request_follow_up")


if __name__ == "__main__":
    unittest.main()
