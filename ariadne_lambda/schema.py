from typing import Any, Literal

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
        lowered_key_headers = {key.lower(): value for key, value in event["headers"].items()}
        request_data = {
            "event": event,
            "body": "",
            "is_base64_encoded": event["isBase64Encoded"],
            "headers": lowered_key_headers,
            "params": event["queryStringParameters"],
        }

        if http_context := event["requestContext"].get("http"):
            # Api Gateway V2
            request_data["path"] = http_context["path"]
            request_data["method"] = http_context["method"].upper()

        else:
            # API Gateway V1
            # Application Load Balancer
            request_data["path"] = event["path"]
            request_data["method"] = event["httpMethod"].upper()

        if body := event["body"]:
            request_data["body"] = body

        if not request_data["params"]:
            request_data["params"] = {}

        return cls(**request_data)


class Response:
    status_code: int
    body: str
    headers: dict

    def __init__(self, status_code: int = 200, body: str = "", headers: dict | None = None):
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
