from typing import Any, Literal, cast

from pydantic import BaseModel


class Request(BaseModel):
    event: dict[str, Any]

    path: str
    method: Literal["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]

    body: str
    is_base64_encoded: bool

    headers: dict[str, str]
    params: dict[str, str]

    @property
    def route_key(self):
        return f"{self.method} {self.path}"

    @classmethod
    def create_from_event(cls, event: dict[str, Any]) -> "Request":
        # this is needed for API Gateway V1 when header keys comes capitalized
        # but on API Gateway V2 it comes as lowered
        headers = cast(dict[str, str], event.get("headers") or {})
        lowered_key_headers = {key.lower(): value for key, value in headers.items()}

        query_params = cast(dict[str, str] | None, event.get("queryStringParameters"))
        params = query_params or {}

        if http_context := event["requestContext"].get("http"):
            # Api Gateway V2
            path = cast(str, http_context["path"])
            raw_method = cast(str, http_context["method"])
        else:
            # API Gateway V1
            # Application Load Balancer
            path = cast(str, event["path"])
            raw_method = cast(str, event["httpMethod"])

        method = cast(
            Literal["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"],
            raw_method.upper(),
        )

        body = cast(str | None, event.get("body")) or ""

        return cls(
            event=event,
            path=path,
            method=method,
            body=body,
            is_base64_encoded=bool(event.get("isBase64Encoded", False)),
            headers=lowered_key_headers,
            params=params,
        )


class Response:
    status_code: int
    body: str
    headers: dict

    def __init__(
        self, status_code: int = 200, body: str = "", headers: dict | None = None
    ):
        self.status_code = status_code
        self.body = body
        if not headers:
            headers = {}
        self.headers = headers

    def __iter__(self):
        yield "statusCode", self.status_code
        yield "body", self.body
        yield "headers", self.headers

    def render(self) -> dict:
        return {
            "statusCode": self.status_code,
            "body": self.body,
            "headers": self.headers,
        }
