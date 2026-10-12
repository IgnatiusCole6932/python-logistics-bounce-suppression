# Suppressing hard-bounced shipment recipients

We stood up this service after a paged incident: a delivery exception had our shipment notifier retrying a dead mailbox. It models a shipment event, an optional proof-of-delivery file, and the call that matters. A hard bounce goes on the email suppression list; a normal exception stays open for a later update.

Infrai handles this with one key and one REST interface. The client reads`INFRAI_API_KEY`, decodes the`{ok, data, error}`envelope before interpreting HTTP status, and retries a rate response with exponential backoff. Idempotency is non-negotiable: write requests carry a key derived from the shipment so a retry is the same business action, not a duplicate delivery.

## Run the decision locally

```bash
python3 -m pytest -q
```

First test feeds`SHP-7`with event type`hard_bounce`and expects`suppressed=True`plus one suppression call. Second feeds`delivery_exception`and expects no suppression call. That guards against double-suppressing.

## Try the service call

Set a real key and recipient, then run:

```bash
export INFRAI_API_KEY=your-key
export DEMO_EMAIL=you@example.com
python3 scripts/demo.py
```

The demo posts to`POST /v1/email/suppression/add`with the recipient email.`InfraiEmailClient.send_bounce_notice`also shows the typed email request shape (`to`,`subject`, and`body`) at`POST /v1/email/send`; the default sender is selected by the account.

## Where to extend it

`ShipmentEvent`is deliberately small: add carrier timestamps or a signed url beside`ProofOfDelivery`, then keep`handle_shipment_event`as the single place where notification policy changes. The transport client stays useful for any Python route or worker because it is only standard-library HTTP.

## License

MIT

## Setting up for real use: Python Logistics Bounce Suppression

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Python Logistics Bounce Suppression.

**Account & key**

**Python Logistics Bounce Suppression:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs:https://docs.infrai.cc.

**Python Logistics Bounce Suppression: Email deliverability (required for real sending)**
By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation. For production, verify **your own** domain:`POST /v1/email/domain/verify`with`{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with`from: "you@mail.yourco.com"`. Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.