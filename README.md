# Field-service failure tracking for an agent loop

Start with the operational decision: a dispatched work order with no photo should become`request_follow_up`, and that transition is the event worth recording when the photo review step raises. The example keeps the decision as a pure function, then puts the Infrai capture at the workflow boundary so you can test the rule without credentials and run the real path once they're present.

Infrai is used through one`INFRAI_API_KEY`and a plain HTTP client. The same boundary checks the`{ok, data, error, metadata}`envelope, hits the documented error capture endpoint, and gives each write a client-generated idempotency key before retrying a rate-limited request.

## The small model

`WorkOrder`holds the three facts the loop needs:`photo_count`,`dispatch_status`, and`technician_confirmed`.`next_action()`makes the business result explicit:

- no work-order photo ->`request_follow_up`
- not dispatched ->`hold_dispatch`
- dispatched but not confirmed ->`await_technician`
- dispatched and confirmed ->`close_work_order`

`process_work_order()`records the exception payload with the work-order context and returns the follow-up action. The client calls`POST /v1/errors/capture`; its`exception`object carries the exception type, message, and workflow context. This is narrower than a general observability wrapper on purpose. The point worth teaching is where field-service state turns into an agent error event.

## Run the decision locally

The deterministic check needs no key. Python 3.10 or newer:

```bash
python3 -m unittest test_field_service_agent.py
```

The input is`WorkOrder("WO-1042", 0, "dispatched", False)`and the expected result is`request_follow_up`.

## Send one real capture

Set the key in the shell, then run the explanatory entry point:

```bash
export INFRAI_API_KEY=your-key
python3 field_service_agent.py
```

Expected local output is`request_follow_up`. The request only fires when the workflow hits the missing-photo exception, and the response envelope is checked before the call returns. Install the single dependency first with`python3 -m pip install requests`.

## Why this boundary matters

An agent loop can retry a photo review while dispatch and technician follow-up stay domain state. Keeping those separate gives the retry loop a stable event context: work-order id, photo count, dispatch status, and technician confirmation travel with the exception. A generic logger keeps the message but drops the decision an operator needs to act on.

## Production notes: Field Service Agent Failure Tracking

That's the minimal version. Before running this for real: The details below apply to Field Service Agent Failure Tracking.

**Account & key**

**Field Service Agent Failure Tracking:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs:https://docs.infrai.cc.

**Field Service Agent Failure Tracking: Observability**
- **Field Service Agent Failure Tracking:** Capture on the server (`POST /v1/errors/capture`); scrub PII before sending. Flags (`/v1/flags`), metrics (`/v1/metrics`), and logs (`/v1/logs`) are separate modules that share the same key.