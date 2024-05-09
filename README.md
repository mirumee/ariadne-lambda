# Ariadne AWS Lambda Extension

This package extends the Ariadne library by adding a GraphQL HTTP handler designed for use in AWS Lambda environments. It enables easy integration of GraphQL services with AWS serverless infrastructure, making it straightforward to deploy GraphQL APIs without worrying about the underlying server management.

## Introduction

This project provides an extension to the Ariadne GraphQL library, specifically tailored for deploying GraphQL APIs on AWS Lambda. It simplifies handling GraphQL requests by providing a custom HTTP handler that seamlessly integrates with the AWS Lambda and API Gateway, allowing developers to focus on their GraphQL schema and resolvers instead of server and infrastructure management.

## Installation

To install the extension, use pip:

```bash
pip install ariadne-lambda
```

## Quick Start

Here's a basic example of how to use the extension in your AWS Lambda function:

```python
from typing import Any

from ariadne import QueryType, gql, make_executable_schema
from ariadne_lambda.graphql import GraphQLLambda
from asgiref.sync import async_to_sync
from aws_lambda_powertools.utilities.typing import LambdaContext

type_defs = gql(
    """
    type Query {
        hello: String!
    }
"""
)
query = QueryType()


@query.field("hello")
def resolve_hello(_, info):
    request = info.context["request"]
    user_agent = request.headers.get("user-agent", "guest")
    return "Hello, %s!" % user_agent


schema = make_executable_schema(type_defs, query)
graphql_app = GraphQLLambda(schema=schema)


def graphql_http_handler(event: dict[str, Any], context: LambdaContext):
    return async_to_sync(graphql_app)(event, context)
```

## Documentation

For full documentation on Ariadne, visit [Ariadne's Documentation](https://ariadnegraphql.org/docs/). For details on AWS Lambda, refer to the [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html).

## Features

- Easy integration with AWS Lambda and API Gateway.
- Support for GraphQL queries and mutations.
- Customizable context and error handling.
- Seamless extension of the Ariadne library for serverless applications.

## Contributing

We welcome all contributions to Ariadne! If you've found a bug or issue, feel free to use [GitHub issues](https://github.com/mirumee/ariadne-lambda/issues). If you have any questions or feedback, don't hesitate to catch us on [GitHub discussions](https://github.com/mirumee/ariadne/discussions/).

For guidance and instructions, please see [CONTRIBUTING.md](CONTRIBUTING.md).

Also make sure you follow [@AriadneGraphQL](https://twitter.com/AriadneGraphQL) on Twitter for latest updates, news and random musings!

**Crafted with ❤️ by [Mirumee Software](http://mirumee.com)**
hello@mirumee.com
