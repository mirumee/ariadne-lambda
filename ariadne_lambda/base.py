from abc import abstractmethod
from inspect import isawaitable
from typing import Any

from ariadne.asgi.handlers.base import GraphQLHandlerBase
from aws_lambda_powertools.utilities.typing import LambdaContext


class GraphQLLambdaHandler(GraphQLHandlerBase):
    @abstractmethod
    async def handle(self, event: dict, context: LambdaContext):  # ty: ignore[invalid-method-override]
        """An entrypoint for the AWS Lambda connection handler.

        This method is called by Ariadne AWS Lambda GraphQL application. Subclasses
        are expected to handle specific event content based on the gateway of invocation
        triggeting the lambda function (e.g. API Gateway, ALB, etc.).

        # Required arguments

        `event`: The AWS Lambda event dictionary.

        `context`: The AWS Lambda context object.
        """
        raise NotImplementedError(
            "Subclasses of GraphQLLambdaHandler must implement the 'handle' method"
        )

    async def get_context_for_request(
        self,
        request: Any,
        data: Any,
    ) -> Any:
        """Return the context value for the request.

        Matches `GraphQLHandlerBase.get_context_for_request`: callable
        `context_value` must accept `(request, data)` (sync or async).

        # Required arguments

        `request`: The request object as defined by the 'handle' method.

        `data`: GraphQL data from connection.
        """
        if callable(self.context_value):
            context = self.context_value(request, data)

            if isawaitable(context):
                context = await context
            return context

        return self.context_value or {"request": request}
