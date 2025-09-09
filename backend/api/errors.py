# backend/api/errors.py
from __future__ import annotations

from typing import Any, Dict
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException
import logging


class ApiError(Exception):
    def __init__(self, status_code: int, message: str, payload: Dict[str, Any] | None = None):
        super().__init__(message)
        self.status_code = int(status_code)
        self.message = message
        self.payload = payload or {}


def api_error(status_code: int, message: str, payload: Dict[str, Any] | None = None):
    raise ApiError(status_code, message, payload)


def register_error_handlers(app: Flask) -> None:
    logger = logging.getLogger(__name__)
    @app.errorhandler(ApiError)
    def _handle_api_error(err: ApiError):
        resp = {"error": err.message, **(err.payload or {})}
        return jsonify(resp), err.status_code

    @app.errorhandler(HTTPException)
    def _handle_http_error(err: HTTPException):
        resp = {"error": err.description or err.name}
        return jsonify(resp), err.code or 500

    @app.errorhandler(Exception)
    def _handle_unexpected(err: Exception):
        logger.exception("Unhandled exception")
        resp = {"error": "Internal Server Error"}
        return jsonify(resp), 500
