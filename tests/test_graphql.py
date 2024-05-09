from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from graphql import GraphQLSchema

from ariadne_lambda.graphql import GraphQLLambda
from ariadne_lambda.http_handler import GraphQLAWSAPIHTTPGatewayHandler


@pytest.fixture
def schema():
    return GraphQLSchema()


@pytest.fixture
def http_handler_mock():
    return MagicMock(spec=GraphQLAWSAPIHTTPGatewayHandler)


@pytest.fixture
def event():
    return {
        "httpMethod": "POST",
        "body": '{"query": "{ testQuery }"}',
        "headers": {"Content-Type": "application/json"},
    }


@pytest.fixture
def context():
    return {}


@pytest.mark.asyncio
@patch("ariadne_lambda.graphql.GraphQLAWSAPIHTTPGatewayHandler")
async def test_graphql_lambda_initialization(http_handler_class_mock, schema):
    # Given
    http_handler_instance_mock = http_handler_class_mock.return_value

    # When
    GraphQLLambda(schema)

    # Then
    http_handler_class_mock.assert_called_once()
    http_handler_instance_mock.configure.assert_called_once()


@pytest.mark.asyncio
async def test_graphql_lambda_call(schema, event, context, http_handler_mock):
    # Given
    http_handler_mock.handle = AsyncMock(
        return_value={"statusCode": 200, "body": '{"data": {"test": "value"}}'}
    )
    graphql_lambda = GraphQLLambda(schema, http_handler=http_handler_mock)

    # When
    response = await graphql_lambda(event, context)

    # Then
    http_handler_mock.handle.assert_called_once_with(event, context)
    assert response == {"statusCode": 200, "body": '{"data": {"test": "value"}}'}
