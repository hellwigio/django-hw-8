import logging


http_logger = logging.getLogger("project.http")


class HttpRequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        http_logger.info("%s %r %d", request.method, request.path, response.status_code)
        return response
