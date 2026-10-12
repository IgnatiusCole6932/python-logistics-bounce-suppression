import os

from src.suppression_service import InfraiEmailClient, ProofOfDelivery, ShipmentEvent, handle_shipment_event


def main() -> None:
    email = os.environ.get("DEMO_EMAIL")
    if not email:
        raise SystemExit("Set DEMO_EMAIL to a recipient before running the demo")
    event = ShipmentEvent(
        shipment_id="SHP-1042",
        recipient_email=email,
        event_type="hard_bounce",
        occurred_at="2026-09-05T09:00:00Z",
        proof=ProofOfDelivery("pod-1042.pdf", "application/pdf", "shipments/SHP-1042/pod.pdf"),
        exception_note="Mailbox rejected delivery",
    )
    result = handle_shipment_event(event, InfraiEmailClient())
    print(result)


if __name__ == "__main__":
    main()
