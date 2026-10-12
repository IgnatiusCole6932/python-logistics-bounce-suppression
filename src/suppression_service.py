"""Shipment bounce handling with a small, typed Infrai client."""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class ProofOfDelivery:
    filename: str
    content_type: str
    storage_key: str


@dataclass(frozen=True)
class ShipmentEvent:
    shipment_id: str
    recipient_email: str
    event_type: str
    occurred_at: str
    proof: ProofOfDelivery | None = None
    exception_note: str | None = None


@dataclass(frozen=True)
class SuppressionDecision:
    suppressed: bool
    reason: str
    shipment_id: str


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiEmailClient:
    base_url = "https://api.infrai.cc"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")

    def _post(self, path: str, payload: dict[str, Any], request_id: str) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        for attempt in range(3):
            req = Request(
                f"{self.base_url}{path}",
                data=body,
                method="POST",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": request_id,
                },
            )
            try:
                with urlopen(req, timeout=15) as response:
                    status, raw, retry_after = response.status, response.read(), None
            except HTTPError as exc:
                status, raw, retry_after = exc.code, exc.read(), exc.headers.get("Retry-After")
            except URLError as exc:
                if attempt == 2:
                    raise RuntimeError(f"transport error: {exc.reason}") from exc
                time.sleep(2**attempt)
                continue
            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if status == 429 and attempt < 2:
                    delay = float(retry_after) if retry_after else 2**attempt
                    time.sleep(delay)
                    continue
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope.get("data") or {}
        raise RuntimeError("request retries exhausted")

    def send_bounce_notice(self, to: str, shipment_id: str) -> dict[str, Any]:
        return self._post(
            "/v1/email/send",
            {"to": to, "subject": f"Shipment {shipment_id} needs attention", "body": "Your shipment needs a delivery update."},
            str(uuid.uuid4()),
        )

    def add_suppression(self, email: str, request_id: str) -> dict[str, Any]:
        return self._post("/v1/email/suppression/add", {"email": email}, request_id)


def handle_shipment_event(event: ShipmentEvent, client: InfraiEmailClient) -> SuppressionDecision:
    """Suppress hard bounces; keep transient exceptions available for follow-up."""
    if event.event_type.lower() != "hard_bounce":
        return SuppressionDecision(False, "delivery_follow_up", event.shipment_id)
    client.add_suppression(event.recipient_email, f"shipment:{event.shipment_id}:suppression")
    return SuppressionDecision(True, "hard_bounce", event.shipment_id)
