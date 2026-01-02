"""Request Logging Middleware.

Logs all API requests to the database for admin monitoring.
"""

import time
import json
from typing import Optional, Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from src.clients.supabase_client import get_supabase_admin_client


# Paths to exclude from logging
EXCLUDED_PATHS = {
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/favicon.ico",
}


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all API requests for admin monitoring."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip excluded paths
        if request.url.path in EXCLUDED_PATHS or request.url.path.startswith("/docs"):
            return await call_next(request)

        # Start timing
        start_time = time.time()

        # Get request details
        method = request.method
        path = request.url.path
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")[:500]  # Limit length

        # Try to extract user_id from authorization header
        user_id = await self._extract_user_id(request)

        # Get request body for POST/PUT/PATCH (with size limit)
        request_body = None
        if method in ("POST", "PUT", "PATCH"):
            try:
                body = await request.body()
                if len(body) < 10000:  # Only log if < 10KB
                    request_body = json.loads(body.decode("utf-8"))
                    # Remove sensitive fields
                    for key in ["password", "api_key", "secret", "token"]:
                        if key in request_body:
                            request_body[key] = "[REDACTED]"
            except Exception:
                request_body = None

        # Process the request
        response = None
        error_message = None
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            error_message = str(e)[:1000]
            raise
        finally:
            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)

            # Log to database (fire and forget)
            await self._log_request(
                user_id=user_id,
                method=method,
                path=path,
                status_code=status_code,
                response_time_ms=response_time_ms,
                ip_address=ip_address,
                user_agent=user_agent,
                request_body=request_body,
                error_message=error_message,
            )

        return response

    async def _extract_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from JWT token in Authorization header."""
        try:
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                from src.clients.supabase_client import get_supabase_client

                supabase = get_supabase_client()
                user = supabase.auth.get_user(token)
                if user and user.user:
                    return user.user.id
        except Exception:
            pass
        return None

    async def _log_request(
        self,
        user_id: Optional[str],
        method: str,
        path: str,
        status_code: int,
        response_time_ms: int,
        ip_address: Optional[str],
        user_agent: str,
        request_body: Optional[dict],
        error_message: Optional[str],
    ) -> None:
        """Log request to database."""
        try:
            supabase = get_supabase_admin_client()

            log_data = {
                "user_id": user_id,
                "method": method,
                "path": path,
                "status_code": status_code,
                "response_time_ms": response_time_ms,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "request_body": request_body,
                "error_message": error_message,
            }

            supabase.table("api_request_logs").insert(log_data).execute()

        except Exception as e:
            # Don't fail the request if logging fails
            print(f"[MIDDLEWARE] Failed to log request: {e}")
