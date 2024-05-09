import json
from inspect import isawaitable
from typing import Any

from ariadne.constants import (
    DATA_TYPE_JSON,
    DATA_TYPE_MULTIPART,
)
from ariadne.exceptions import HttpBadRequestError, HttpError
from ariadne.explorer import Explorer
from ariadne.graphql import graphql
from ariadne.types import (
    ContextValue,
    ExtensionList,
    Extensions,
    GraphQLResult,
    Middlewares,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from graphql import DocumentNode, MiddlewareManager

from ariadne_lambda.base import GraphQLLambdaHandler
from ariadne_lambda.schema import Request, Response


class GraphQLAWSAPIHTTPGatewayHandler(GraphQLLambdaHandler):
    """Handler for AWS Lambda functions triggered by HTTP requests via API Gateway.

    Designed to process both Query and Mutation operations in a GraphQL schema.
    Ideal for serverless architectures, providing a bridge between AWS Lambda and GraphQL.
    """

    def __init__(
        self,
        extensions: Extensions | None = None,
        middleware: Middlewares | None = None,
        middleware_manager_class: type[MiddlewareManager] | None = None,
    ) -> None:
        super().__init__()

        self.extensions = extensions
        self.middleware = middleware
        self.middleware_manager_class = middleware_manager_class or MiddlewareManager

    async def handle(self, event: dict, context: LambdaContext):
        """Processes AWS Lambda event triggered by an API Gateway HTTP request.

        Extracts the HTTP request from the Lambda event,
        and delegates to the appropriate handler based on the HTTP method.
        """
        request = Request.create_from_event(event)
        return (await self.handle_request(request)).render()

    async def handle_request(self, request: Request) -> Response:
        """Determines the request type (GET or POST) and routes to the corresponding GraphQL
        processor.
        Supports executing queries directly from GET requests, or handling
        introspection and GraphQL explorers."""
        if request.method == "GET":
            if self.execute_get_queries and request.params and request.params.get("query"):
                return await self.graphql_http_server(request)
            if self.introspection and self.explorer:
                # only render explorer when introspection is enabled
                return await self.render_explorer(request, self.explorer)

        if request.method == "POST":
            return await self.graphql_http_server(request)

        return self.handle_not_allowed_method(request)

    async def render_explorer(self, request: Request, explorer: Explorer) -> Response:
        """Return a HTML response with GraphQL explorer.

        # Required arguments:

        `request`: the `Request` instance from Starlette or FastAPI.

        `explorer`: an `Explorer` instance that implements the
        `html(request: Request)` method which returns either the `str` with HTML
        or `None`. If explorer returns `None`, `405` method not allowed response
        is returned instead.
        """
        explorer_html = explorer.html(request)
        if isawaitable(explorer_html):
            explorer_html = await explorer_html
        if explorer_html:
            return Response(body=explorer_html, headers={"Content-Type": "text/html"})

        return self.handle_not_allowed_method(request)

    async def graphql_http_server(self, request: Request) -> Response:
        """Executes GraphQL queries or mutations based on the POST request's body.

        Parses the request, executes the GraphQL query, and formats the response as JSON.
        """
        try:
            data = await self.extract_data_from_request(request)
        except HttpError as error:
            return Response(
                status_code=400,
                body=error.message or error.status,
                headers={"Content-Type": "text/plain"},
            )

        success, result = await self.execute_graphql_query(request, data)
        return await self.create_json_response(request, result, success)

    async def extract_data_from_request(self, request: Request):
        """
        Executes a GraphQL query or mutation based on the parsed request data.

        This method processes the GraphQL request, executes the query or mutation,
        and returns the results in a JSON-formatted response suitable for
        AWS Lambda's HTTP response format.

        Args:
            request: A `Request` object containing the parsed HTTP request from API Gateway.

        Returns:
            A `Response` object containing the JSON-formatted result of the GraphQL operation.
        """
        content_type = request.headers.get("content-type", "")
        content_type = content_type.split(";")[0]

        if content_type == DATA_TYPE_JSON:
            return await self.extract_data_from_json_request(request)
        if content_type == DATA_TYPE_MULTIPART:
            return await self.extract_data_from_multipart_request(request)
        if (
            request.method == "GET"
            and self.execute_get_queries
            and request.params
            and request.params.get("query")
        ):
            return self.extract_data_from_get_request(request)

        raise HttpBadRequestError(
            "Posted content must be of type {} or {}".format(  # noqa: UP032
                DATA_TYPE_JSON, DATA_TYPE_MULTIPART
            )
        )

    async def extract_data_from_json_request(self, request: Request) -> dict:
        """
        Parses the JSON body of an HTTP request to extract the GraphQL query data.

        Args:
            request: A `Request` object containing the parsed HTTP request from API Gateway.

        Returns:
            A dictionary containing the extracted GraphQL query data.

        Raises:
            HttpBadRequestError: If the request body is not valid JSON.
        """
        try:
            return json.loads(request.body)
        except (TypeError, ValueError) as ex:
            raise HttpBadRequestError("Request body is not a valid JSON") from ex

    async def extract_data_from_multipart_request(self, request: Request):
        raise NotImplementedError("Multipart requests are not yet supported in AWS Lambda")

    def extract_data_from_get_request(self, request: Request) -> dict:
        """
        Extracts the GraphQL query data from the query string parameters of a GET request.

        Args:
            request: A `Request` object containing the parsed HTTP request from API Gateway.

        Returns:
            A dictionary containing the GraphQL query, operation name, and variables.

        Raises:
            HttpBadRequestError: If the query parameters are missing or invalid.
        """
        if not request.params:
            raise HttpBadRequestError("Query variables are not valid")
        query = request.params["query"].strip()
        operation_name = request.params.get("operationName", "").strip()
        variables = request.params.get("variables", "").strip()

        clean_variables = None

        if variables:
            try:
                clean_variables = json.loads(variables)
            except (TypeError, ValueError) as ex:
                raise HttpBadRequestError("Variables query arg is not a valid JSON") from ex

        return {
            "query": query,
            "operationName": operation_name or None,
            "variables": clean_variables,
        }

    async def execute_graphql_query(
        self,
        request: Any,
        data: Any,
        *,
        context_value: Any = None,
        query_document: DocumentNode | None = None,
    ) -> GraphQLResult:
        """
        Executes the GraphQL query using the provided data and optional context.

        Args:
            request: The request object, typically containing metadata and headers.
            data: A dictionary containing the query, variables, and operation name.
            context_value: Optional context passed to the GraphQL execution.
            query_document: An optional pre-parsed GraphQL query document.

        Returns:
            A `GraphQLResult` object containing the results of the query execution.
        """
        if context_value is None:
            context_value = await self.get_context_for_request(request, data)

        extensions = await self.get_extensions_for_request(request, context_value)
        # TODO: figure out how to mix those with powertools middleware
        # middleware = await self.get_middleware_for_request(request, context_value)
        middleware = None

        if self.schema is None:
            raise TypeError("schema is not set, call configure method to initialize it")

        if isinstance(request, Request):
            require_query = request.method == "GET"
        else:
            require_query = False

        return await graphql(
            self.schema,
            data,
            context_value=context_value,
            root_value=self.root_value,
            query_parser=self.query_parser,
            query_validator=self.query_validator,
            query_document=query_document,
            validation_rules=self.validation_rules,
            require_query=require_query,
            debug=self.debug,
            introspection=self.introspection,
            logger=self.logger,
            error_formatter=self.error_formatter,
            extensions=extensions,
            middleware=middleware,
            middleware_manager_class=self.middleware_manager_class,
            execution_context_class=self.execution_context_class,
        )

    async def get_extensions_for_request(
        self, request: Any, context: ContextValue | None
    ) -> ExtensionList:
        """
        Determines the extensions to be used for the current GraphQL request.

        Args:
            request: The request object, providing access to request-specific data.
            context: Optional context associated with the request.

        Returns:
            A list of extensions to be used during the execution of the GraphQL query.
        """
        if callable(self.extensions):
            extensions = self.extensions(request, context)
            if isawaitable(extensions):
                extensions = await extensions  # type: ignore
            return extensions
        return self.extensions

    async def create_json_response(
        self,
        request: Request,  # pylint: disable=unused-argument
        result: dict,
        success: bool,
    ) -> Response:
        """
        Formats the GraphQL execution result into a JSON response suitable for AWS Lambda.

        Args:
            request: The original request object.
            result: The result dictionary from GraphQL execution.
            success: A boolean flag indicating if the query execution was successful.

        Returns:
            A `Response` object containing the JSON-formatted GraphQL result.
        """
        status_code = 200 if success else 400
        return Response(
            status_code=status_code,
            body=json.dumps(result),
            headers={"Content-Type": "application/json"},
        )

    def handle_not_allowed_method(self, request: Request):
        """
        Generates a response for HTTP methods not supported by the GraphQL handler.

        This method is typically invoked for HTTP methods other than GET or POST, or
        when the GraphQL endpoint is configured to reject certain types of requests.

        Args:
            request: The original request object.

        Returns:
            A `Response` object indicating the HTTP method is not allowed.
        """
        allowed_methods = ["OPTIONS", "POST"]
        if self.introspection:
            allowed_methods.append("GET")
        allow_header = {"Allow": ", ".join(allowed_methods)}

        if request.method == "OPTIONS":
            return Response(headers=allow_header)

        return Response(status_code=405, headers=allow_header)
