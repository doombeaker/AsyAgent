from __future__ import annotations


class AsyAgentError(Exception):
    status: int = 500
    code: str = "internal_error"

    def __init__(self, message: str, *, detail: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail

    def to_dict(self) -> dict:
        body = {"error": {"code": self.code, "message": self.message}}
        if self.detail:
            body["error"]["detail"] = self.detail
        return body


class BadRequest(AsyAgentError):
    status = 400
    code = "bad_request"


class NotFound(AsyAgentError):
    status = 404
    code = "not_found"


class UnsupportedFormat(BadRequest):
    code = "unsupported_format"


class EmptyInput(BadRequest):
    code = "empty_input"


class InvalidInput(BadRequest):
    code = "invalid_input"


class InputTooLarge(BadRequest):
    code = "input_too_large"


class MissingStorage(BadRequest):
    status = 409
    code = "storage_unavailable"


class FetchError(AsyAgentError):
    status = 502
    code = "fetch_failed"


class CompileError(AsyAgentError):
    status = 422
    code = "compile_failed"


class RasterError(AsyAgentError):
    status = 502
    code = "raster_failed"


class CompileTimeout(AsyAgentError):
    status = 504
    code = "timeout"


class StorageError(AsyAgentError):
    status = 502
    code = "storage_failed"


class ServerBusy(AsyAgentError):
    status = 503
    code = "server_busy"
