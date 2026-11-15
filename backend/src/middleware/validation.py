from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


async def validation_error_response(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "loc": error.get("loc", ()),
                "type": error.get("type", "value_error"),
                "msg": error.get("msg", "Invalid value"),
            }
        )
    return JSONResponse(status_code=422, content={"detail": errors})
