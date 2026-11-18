from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def _safe_validation_message(error: dict) -> str:
    error_type = error.get("type", "value_error")
    location = error.get("loc", ())
    field = str(location[-1]) if location else ""

    if error_type == "missing":
        return "Field required."
    if field == "email" and error_type == "value_error":
        return "Enter a valid email address."
    if field in {"password", "new_password", "current_password"}:
        if "password must not exceed 72 bytes" in str(error.get("ctx", {}).get("error", "")):
            return "Password must not exceed 72 bytes."
        if error_type == "string_too_short":
            return "Password is too short."
        if error_type == "string_too_long":
            return "Password exceeds the maximum length."
        if error_type == "value_error":
            return "Password does not meet the requirements."
    if error_type == "string_too_short":
        return "Value is too short."
    if error_type == "string_too_long":
        return "Value is too long."
    if error_type == "string_pattern_mismatch":
        return "Value has an invalid format."
    return "Invalid value."


async def validation_error_response(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "loc": error.get("loc", ()),
                "type": error.get("type", "value_error"),
                "msg": _safe_validation_message(error),
            }
        )
    return JSONResponse(status_code=422, content={"detail": errors})
