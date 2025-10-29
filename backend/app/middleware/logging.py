"""Custom logging middleware for Starlette."""

import time


class LoggingMiddleware:
    """Middleware that logs HTTP requests and responses."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        start_time = time.time()

        if scope['type'] == 'http':
            print(f"Request: {scope.get('method')} {scope.get('path')}")

        async def send_wrapper(message):
            if message['type'] == 'http.response.start':
                process_time = time.time() - start_time
                print(f"Response: {message['status']} in {process_time:.2f}s")
            await send(message)

        await self.app(scope, receive, send_wrapper)
