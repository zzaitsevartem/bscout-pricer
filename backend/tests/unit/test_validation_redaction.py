import httpx
import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from src.middleware.validation import validation_error_response
from src.modules.auth.schema.auth import LoginRequest, RefreshRequest, RegisterRequest

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("schema", "body"),
    [
        (RegisterRequest, {"email": "bad", "full_name": "", "password": "secret"}),
        (RegisterRequest, {"email": "bad", "full_name": "name", "password": "secret" * 30}),
        (LoginRequest, {"identifier": "", "password": {"secret": "secret"}}),
        (RefreshRequest, {"refresh_token": {"secret": "secret"}}),
    ],
)
async def test_validation_does_not_echo_input_or_context(schema, body, caplog):
    app = FastAPI()
    app.add_exception_handler(RequestValidationError, validation_error_response)

    async def endpoint(body: schema):
        return {"ok": True}

    app.post("/test")(endpoint)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://test") as c:
        response = await c.post("/test", json=body)
    assert response.status_code == 422
    assert "secret" not in response.text
    errors = response.json()["detail"]
    assert errors
    assert all(set(error) == {"loc", "type", "msg"} for error in errors)
    assert "secret" not in caplog.text
