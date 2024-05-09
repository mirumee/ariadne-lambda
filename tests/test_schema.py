from ariadne_lambda.schema import Request, Response


def test_api_v1_event(api_gateway_v1_event_payload):
    lowered_keys_headers = {
        key.lower(): value for key, value in api_gateway_v1_event_payload["headers"].items()
    }
    request = Request.create_from_event(api_gateway_v1_event_payload)
    assert request.method == api_gateway_v1_event_payload["httpMethod"]
    assert request.path == api_gateway_v1_event_payload["path"]
    assert request.body == ""
    assert request.is_base64_encoded is False
    assert request.headers == lowered_keys_headers
    assert request.params == api_gateway_v1_event_payload["queryStringParameters"]


def test_api_v2_event(api_gateway_v2_event_payload):
    request = Request.create_from_event(api_gateway_v2_event_payload)
    assert request.method == api_gateway_v2_event_payload["requestContext"]["http"]["method"]
    assert request.path == api_gateway_v2_event_payload["requestContext"]["http"]["path"]
    assert request.body == ""
    assert request.is_base64_encoded is False
    assert request.headers == api_gateway_v2_event_payload["headers"]
    assert request.params == api_gateway_v2_event_payload["queryStringParameters"]


def test_response_initialization():
    # When
    response = Response(status_code=200, body="OK", headers={"Content-Type": "application/json"})

    # Then
    assert response.status_code == 200
    assert response.body == "OK"
    assert response.headers == {"Content-Type": "application/json"}


def test_response_default_values():
    # When
    response = Response()

    # Then
    assert response.status_code == 200
    assert response.body == ""
    assert response.headers == {}


def test_response_iter():
    # When
    response = Response(status_code=404, body="Not Found", headers={"X-Custom-Header": "value"})
    response_dict = dict(response)

    # Then
    assert response_dict == {
        "statusCode": 404,
        "body": "Not Found",
        "headers": {"X-Custom-Header": "value"},
    }


def test_response_render():
    # When
    response = Response(status_code=500, body="Error", headers={"Content-Type": "text/plain"})
    response_rendered = response.render()

    # Then
    assert response_rendered == {
        "statusCode": 500,
        "body": "Error",
        "headers": {"Content-Type": "text/plain"},
    }
