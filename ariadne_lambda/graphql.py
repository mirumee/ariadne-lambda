from logging import Logger, LoggerAdapter
from typing import Any

from ariadne.explorer import Explorer, ExplorerGraphiQL
from ariadne.format_error import format_error
from ariadne.types import (
    ContextValue,
    ErrorFormatter,
    QueryParser,
    QueryValidator,
    RootValue,
    ValidationRules,
)
from graphql import ExecutionContext, GraphQLSchema

from ariadne_lambda.base import GraphQLLambdaHandler
from ariadne_lambda.http_handler import GraphQLAWSAPIHTTPGatewayHandler


class GraphQLLambda:
    def __init__(
        self,
        schema: GraphQLSchema,
        *,
        context_value: ContextValue | None = None,
        root_value: RootValue | None = None,
        query_parser: QueryParser | None = None,
        query_validator: QueryValidator | None = None,
        validation_rules: ValidationRules | None = None,
        execute_get_queries: bool = False,
        debug: bool = False,
        introspection: bool = True,
        explorer: Explorer | None = None,
        logger: None | str | Logger | LoggerAdapter = None,
        error_formatter: ErrorFormatter = format_error,
        execution_context_class: type[ExecutionContext] | None = None,
        http_handler: GraphQLLambdaHandler | None = None,
    ) -> None:
        if http_handler:
            self.http_handler = http_handler
        else:
            self.http_handler = GraphQLAWSAPIHTTPGatewayHandler()

        if not explorer:
            explorer = ExplorerGraphiQL()

        self.http_handler.configure(
            schema,
            context_value,
            root_value,
            query_parser,
            query_validator,
            validation_rules,
            execute_get_queries,
            debug,
            introspection,
            explorer,
            logger,
            error_formatter,
            execution_context_class,
        )

    async def __call__(self, event: dict, context: Any) -> dict:
        response = await self.http_handler.handle(event, context)
        return response
