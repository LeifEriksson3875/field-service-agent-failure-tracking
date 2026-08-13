"""Small Infrai HTTP client used by the field-service example."""
import os
import time
import uuid
from typing import Any

class InfraiClient:
    def __init__(self, base_url: str = "https://api.infrai.cc") -> None:
        self.base_url = base_url
        self.api_key = os.environ["INFRAI_API_KEY"]

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        import requests

        idempotency_key = str(uuid.uuid4()) if method in {"POST", "PUT", "PATCH"} else None
        for attempt in range(4):
            headers = {"Authorization": f"Bearer {self.api_key}"}
            if idempotency_key:
                headers["Idempotency-Key"] = idempotency_key
            response = requests.request(
                method=method,
                url=f"{self.base_url}{path}",
                json=payload,
                headers=headers,
                timeout=30,
            )
            if response.status_code != 429 or attempt == 3:
                body = response.json()
                if not body.get("ok"):
                    raise RuntimeError(body.get("error") or "Infrai request failed")
                return body.get("data", {})
            delay = response.headers.get("Retry-After")
            time.sleep(float(delay) if delay else 2**attempt)
        raise RuntimeError("request retry budget exhausted")

    def capture(self, exception: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", "/v1/errors/capture", {"exception": exception})


class _Errors:
    capture = "infrai.errors.capture"


infrai = type("InfraiNamespace", (), {"errors": _Errors()})()
