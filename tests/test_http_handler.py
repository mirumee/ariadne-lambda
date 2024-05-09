from unittest.mock import AsyncMock, MagicMock

import pytest

from ariadne_lambda.http_handler import (
    GraphQLAWSAPIHTTPGatewayHandler,
    Request,
    Response,
)


@pytest.fixture
def handler():
    handler = GraphQLAWSAPIHTTPGatewayHandler()
    handler.schema = MagicMock()
    handler.execute_graphql_query = AsyncMock()
    return handler


@pytest.mark.asyncio
async def test_handle(handler, api_gateway_v1_event_payload, lambda_context):
    # Given
    mocked_handler_request = AsyncMock(return_value=Response(body="response", status_code=200))
    handler.handle_request = mocked_handler_request

    # When
    result = await handler.handle(api_gateway_v1_event_payload, lambda_context)

    # Then
    mocked_handler_request.assert_called_once()
    assert result["statusCode"] == 200
    assert result["body"] == "response"


@pytest.mark.asyncio
async def test_handle_request_post_graphql(handler, api_gateway_v1_event_payload):
    # Given
    request = Request.create_from_event(api_gateway_v1_event_payload)
    request.method = "POST"
    mocked_graphql_http_server = AsyncMock(return_value=Response(body="response", status_code=200))
    handler.graphql_http_server = mocked_graphql_http_server

    # When
    response = await handler.handle_request(request)

    # Then
    mocked_graphql_http_server.assert_called_once()
    assert response.status_code == 200
    assert "response" == response.body


@pytest.mark.asyncio
async def test_handle_request_get_explorer(handler, api_gateway_v1_event_payload):
    # Given
    handler.introspection = True
    handler.explorer = True
    mocked_render_explorer = AsyncMock(return_value=Response(body="response", status_code=200))
    handler.render_explorer = mocked_render_explorer
    request = Request.create_from_event(api_gateway_v1_event_payload)

    # When
    response = await handler.handle_request(request)

    # Then
    mocked_render_explorer.assert_called_once()
    assert response.status_code == 200
    assert "response" == response.body


@pytest.mark.asyncio
async def test_handle_request_method_not_allowed(handler, api_gateway_v1_event_payload):
    # Given
    request = Request.create_from_event(api_gateway_v1_event_payload)
    request.method = "PUT"
    mocked_handle_not_allowed_method = MagicMock(
        return_value=Response(body="Method Not Allowed", status_code=405)
    )
    handler.handle_not_allowed_method = mocked_handle_not_allowed_method

    # Then
    response = await handler.handle_request(request)

    # Then
    mocked_handle_not_allowed_method.assert_called_once()
    assert response.status_code == 405
    assert "Method Not Allowed" in response.body


@pytest.mark.asyncio
async def test_handle_request_get_graphql_http_server(handler, api_gateway_v1_event_payload):
    # Given
    handler.execute_get_queries = True
    mocked_graphql_http_server = AsyncMock(return_value=Response(body="response", status_code=200))
    handler.graphql_http_server = mocked_graphql_http_server
    request = Request.create_from_event(api_gateway_v1_event_payload)
    request.params = {"query": "hello"}

    # When
    response = await handler.handle_request(request)

    # Then
    mocked_graphql_http_server.assert_called_once()
    assert response.status_code == 200
    assert "response" == response.body


@pytest.mark.asyncio
async def test_render_explorer_enabled(handler, api_gateway_v1_event_payload):
    # Given
    request = Request.create_from_event(api_gateway_v1_event_payload)
    mocked_explorer = MagicMock()
    mocked_explorer.html.return_value = "<div>GraphQL Explorer</div>"
    handler.explorer = mocked_explorer

    # When
    response = await handler.render_explorer(request, handler.explorer)

    # Then
    assert response.status_code == 200
    assert "<div>GraphQL Explorer</div>" in response.body
    assert response.headers["Content-Type"] == "text/html"


@pytest.mark.asyncio
async def test_render_explorer_no_explorer(handler, api_gateway_v1_event_payload):
    # Given
    request = Request.create_from_event(api_gateway_v1_event_payload)
    mocked_explorer = MagicMock()
    mocked_explorer.html.return_value = None
    handler.explorer = mocked_explorer

    # When
    response = await handler.render_explorer(request, handler.explorer)

    # Then
    assert response.status_code == 405
