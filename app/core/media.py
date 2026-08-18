"""Media static serving.

Product image filenames are content-addressed (uuid), so the files are
immutable: browsers and mobile clients may cache them indefinitely. This
subclass adds the corresponding ``Cache-Control`` header on top of
Starlette's default ETag/Last-Modified behaviour.

Media files are already-compressed raster formats; gzip would burn CPU
for nothing, so the middleware below skips ``/media``.
"""

from starlette.middleware.gzip import GZipMiddleware
from starlette.responses import Response
from starlette.staticfiles import StaticFiles

_CACHE_CONTROL = "public, max-age=31536000, immutable"


class CachedStaticFiles(StaticFiles):
    def file_response(
        self, full_path, stat_result, scope, status_code: int = 200
    ) -> Response:
        response = super().file_response(full_path, stat_result, scope, status_code)
        response.headers["Cache-Control"] = _CACHE_CONTROL
        return response


class SkipMediaGZipMiddleware(GZipMiddleware):
    """GZip everything except /media (already-compressed raster images)."""

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["path"].startswith("/media"):
            await self.app(scope, receive, send)
        else:
            await super().__call__(scope, receive, send)
