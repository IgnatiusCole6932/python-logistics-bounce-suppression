from src.suppression_service import ShipmentEvent, SuppressionDecision, handle_shipment_event


class RecordingClient:
    def __init__(self):
        self.calls = []

    def add_suppression(self, email, request_id):
        self.calls.append((email, request_id))
        return {"suppressed": True}


def test_hard_bounce_suppresses_recipient_once():
    client = RecordingClient()
    event = ShipmentEvent("SHP-7", "ops@example.com", "hard_bounce", "2026-09-05T09:00:00Z")
    decision = handle_shipment_event(event, client)
    assert decision == SuppressionDecision(True, "hard_bounce", "SHP-7")
    assert client.calls == [("ops@example.com", "shipment:SHP-7:suppression")]


def test_soft_exception_stays_available():
    client = RecordingClient()
    event = ShipmentEvent("SHP-8", "ops@example.com", "delivery_exception", "2026-09-05T09:00:00Z")
    assert handle_shipment_event(event, client).suppressed is False
    assert client.calls == []
