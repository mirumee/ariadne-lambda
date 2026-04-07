# CHANGELOG

All notable unreleased changes to this project will be documented in this file.

For released versions, see the [Releases](https://github.com/mirumee/ariadne-lambda/releases) page.

## Unreleased

### Breaking Changes

- **Ariadne 1.x is required.** Supported versions are `ariadne>=1.0.1,<2.0.0` (the previous upper bound was `<0.30.0`). Upgrade Ariadne in applications that depend on this package before upgrading `ariadne-lambda`.
- **`GraphQLLambdaHandler` subclasses `GraphQLHandlerBase`.** Ariadne 1.0 renamed the ASGI handler base class from `GraphQLHandler` to `GraphQLHandlerBase`; this package follows that API.
- **Callable `context_value` must use `(request, data)`.** The old fallback for callables that only accepted `(request)` has been removed so behavior matches `GraphQLHandlerBase.get_context_for_request` in Ariadne 1.0.

### Bug Fixes

- **Lambda function URLs:** `Request.create_from_event` accepts HTTP API v2–style events used with **Lambda function URLs** when `queryStringParameters` is missing and `body` is omitted (previously could raise or mis-handle keys).

### Improvements

- Refine request parsing and GraphQL HTTP handling (Pydantic `Request` model, handler tests, and fixtures aligned with API Gateway v2 payloads).

### CI/CD

- Run tests on **Python 3.10–3.14** in a matrix; refresh GitHub Actions (`actions/setup-python`, reusable **test** / **build** / **prepare_release** / **publish** workflows).
- Replace older standalone workflows (`run_tests`, `code_quality`, `deploy`) with the modernized pipeline.

### Build System

- **Hatch** packaging, expanded `pyproject.toml` metadata, optional extras for dev/test/types, and **git-cliff** (`cliff.toml`) for release notes.
- Disable coverage **`fail_under`** until the test suite is expanded (previously targeted 90%).
- Add **`pip`** to the `dev` optional extra so Hatch can install into a uv-managed `.venv` when `[tool.hatch.envs.default] path = ".venv"` is set (Hatch syncs via pip).
- Add **`uv.lock`** for reproducible local and CI installs.

### Documentation

- Declare support for Python 3.10–3.14 in project metadata; update README contact email.

### Testing

- Add API Gateway v2 **Lambda function URL** sample payload and tests; extend HTTP handler and schema tests alongside the refactors above.
