"""
File where is defined the Router class.
"""

from asyncio   import StreamReader, StreamWriter, CancelledError, start_server
from sys       import version_info
from re        import sub
from datetime  import datetime
from .logger   import Logger
from .         import VERSION
from .request  import Request
from .response import Response



class Router:
    """
    Router class to handle HTTP requests.
    Written with asyncio.
    Needs async coroutines for it.
    Enjoy the pain of using it :)
    """

    def __init__(self):
        self.routes = {
            "GET": {},
            "POST": {},
            "PUT": {},
            "DELETE": {},
            "PATCH": {},
            "OPTIONS": {},
        }  # Dictionary to store route handlers
        self.logger = Logger()

        self.host = ""
        self.port = 0
        self.debug = False
        self.middlewares = []
        self.server = None

    def __str__(self):
        return f"HTTP Server on {self.host}:{self.port}, logging to {self.logger.filename}, debug mode : {self.debug}"

    # Definition of all methods (get, post, etc.)
    def get(self, path: str, handler: callable) -> None:
        """
        Register a handler for a GET request on the given path.

        Args:
        path (str): The URL path to handle.
        handler (coroutine function): The async function that handles the request.
        """
        path_pattern = self._path_to_regex(path)
        self.routes["GET"][path_pattern] = handler

    def post(self, path: str, handler: callable) -> None:
        """
        Register a handler for a POST request on the given path.

        Args:
        path (str): The URL path to handle.
        handler (coroutine function): The async function that handles the request.
        """
        path_pattern = self._path_to_regex(path)
        self.routes["POST"][path_pattern] = handler

    def put(self, path: str, handler: callable) -> None:
        """
        Register a handler for a PUT request on the given path.

        Args:
        path (str): The URL path to handle.
        handler (coroutine function): The async function that handles the request.
        """
        path_pattern = self._path_to_regex(path)
        self.routes["PUT"][path_pattern] = handler

    def delete(self, path: str, handler: callable) -> None:
        """
        Register a handler for a DELETE request on the given path.

        Args:
        path (str): The URL path to handle.
        handler (coroutine function): The async function that handles the request.
        """

        path_pattern = self._path_to_regex(path)
        self.routes["DELETE"][path_pattern] = handler

    def patch(self, path: str, handler: callable) -> None:
        """
        Register a handler for a PATCH request on the given path.

        Args:
        path (str): The URL path to handle.
        handler (coroutine function): The async function that handles the request.
        """

        path_pattern = self._path_to_regex(path)
        self.routes["PATCH"][path_pattern] = handler

    def options(self, path: str, handler: callable) -> None:
        """
        Register a handler for a OPTIONS request on the given path.

        Args:
        path (str): The URL path to handle.
        handler (coroutine function): The async function that handles the request.
        """

        path_pattern = self._path_to_regex(path)
        self.routes["OPTIONS"][path_pattern] = handler

    def route(self, method: str, path:str) -> callable:
        """
        Decorator to add a route to the router.

        Args:
        method (str): The HTTP method to handle.
        path (str): The URL path to handle.
        """

        def wrapper(handler: callable):
            self.routes[method][self._path_to_regex(path)] = handler
            return handler
        return wrapper

    def static(self, path: str, directory: str) -> None:
        """
        Serve static files from the given directory.

        Args:
        path (str): The URL path to handle.
        directory (str): The directory to serve static files from.
        """

        path = self._path_to_regex(path + "<name>")
        self.routes["GET"][path] = lambda req, res: res.file(directory + "/" + req.params["name"])

    def add_middleware(self, middleware: callable) -> None:
        """
        Add a middleware to the router.
        The middleware will be called with the request and response objects.
        Needs to be async.
        """
        self.middlewares.append(middleware)

    async def serve(self, port: int=8080, host: str="127.0.0.1", debug: bool=False) -> None:
        """
        Start the event loop to handle requests.
        """
        self.host  = host
        self.port  = port
        self.debug = debug

        try:
            await self.run()
        except KeyboardInterrupt:
            self.shutdown()
        except Exception as e:
            self.logger.error(e)

    async def run(self):
        """
        Real function who starts the server, can't be used by the user, use "serve" instead
        """

        # Await the coroutine to start the server
        self.server = await start_server(
            self.handle_connection, self.host, self.port
        )

        addr = self.server.sockets[0].getsockname()
        if self.debug:
            await self.logger.debug(f"Serving on {addr[0]}:{addr[1]}, PYN v{VERSION}, Python v{version_info.major}.{version_info.minor}.{version_info.micro}")

        # Serve requests until Ctrl+C is pressed
        async with self.server:
            try :
                await self.server.serve_forever()
            except CancelledError:
                pass
            except Exception as e:
                await self.logger.error(e)

    async def handle_connection(self, reader: StreamReader, writer: StreamWriter):
        """
        Handle a client connection.

        Args:
        reader (asyncio.StreamReader): Stream reader object to read data from the client.
        writer (asyncio.StreamWriter): Stream writer object to write data to the client.
        """
        start = datetime.now()

        request_data = await reader.read(1073741824)
        request_text = request_data.decode("utf-8")

        if request_text == "" or request_text is None:
            return

        protocol = request_text.splitlines()[0].split(" ")[0]
        request_line = request_text.splitlines()[0]
        method, path, _ = request_line.split()

        headers = {}
        for line in request_text.splitlines()[1:]:
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()

        body = request_text.split("\r\n\r\n", 1)[1]

        path = path.split("?")[0]
        path = path.split("#")[0]

        info = {
            "protocol": protocol,
            "start":    start,
            "path":     path,
            "method":   method,
            "src_ip":   self.host,
        }

        handler, params = self.get_handler(method, path)

        request = Request(method, path, headers, body, params)
        response = Response(writer, info, self.middlewares, request)

        if handler:
            await handler(request, response)
        else:
            await response.send("404 Not Found\nPath : " + path + " unknown\n", status=404)

    async def shutdown(self):
        """Shitty way to shutdown this mess"""

        if self.server is None:
            exit(0)

        self.server._serving = False
        self.server.close()
        if self.debug:
            await self.logger.debug("Server stopped by user")

    # Helper methods
    def get_handler(self, method, path):
        """Helper method to get the handler for a given method and path, allowing dynamic routing"""
        for pattern, handler in self.routes[method].items():
            match = pattern.match(path)
            if match:
                return handler, match.groupdict()
        return None, {}

    @staticmethod
    def _path_to_regex(path):
        """
        Convert a URL path to a regular expression, allowing dynamic routing.
        Args:
        path (str): The URL path to convert.
        """
        # Remplacer les paramètres par des groupes de capture dans l'expression régulière
        try :
            regex_path = sub(r"<(\w+)>", r"(?P<\1>[^/]+)", path)
            return compile(f'^{regex_path}$')
        except Exception as e:
            Logger().error(e)
