from datetime import datetime
from asyncio  import StreamReader, StreamWriter, CancelledError, start_server, wait_for, TimeoutError, gather, run as run_async
from json     import load, dumps
from re       import sub, compile
from aiofiles import open as aio_open
from hashlib  import sha1
from base64   import b64encode


class Request:
    """
    Request class used to handle HTTP requests. Written with asyncio. You can use real asyncio with "request.reader" if needed (asyncio.StreamReader, but not recommended).
    """
    def __init__(self, method: str, path: str, headers: dict = {}, body: str = "", params: dict = {}):
        self.method = method
        self.path = path
        self.headers = headers
        self.body = body
        self.params = params

    def __str__(self):
        return f"Method : {self.method}\nPath : {self.path}\nHeaders : {self.headers}\nBody : {self.body}\nParams : {self.params}"


class Response:
    """
    Response class used to send HTTP responses to the client. Written with asyncio. You can use real asyncio with "response.writer" if needed (asyncio.StreamWriter, but not recommended).
    """

    def __init__(self, writer: StreamWriter = None, info: dict = {}, middlewares: list[callable] = [], request: Request = None):
        self.writer = writer
        self.logger = Logger()
        self.info = info
        self.middlewares = middlewares
        self.request = request

    def __str__(self):
        try :
            return f"Protocol : {self.info['protocol']} \nSrc IP : {self.info['src_ip']} \nDst IP : {self.writer.transport.get_extra_info('peername')[0]} \nMethod : {self.info['method']} \nPath : {self.info['path']}"
        except Exception as e:
            return "Error : " + type(e).__name__

    async def send(self, content: str = "", status: int=200, content_type: str="text/html") -> None:
        """
        Send an HTTP response to the client.

        Args:
        content (str): The content to send in the HTTP body.
        status (int): The HTTP status code.
        """
        try :
            self.response = {
                "protocol": "HTTP/1.1",
                "status": status,
                "message": self._get_status_message(status),
                "headers": {
                    "Content-Type": f"{content_type}; charset=utf-8",
                    "Connection": "close",
                },
                "body": content,
            }

            await self._run_middlewares()

            headers = "\n".join(
                [f"{key}: {value}" for key, value in self.response["headers"].items()]
            )

            response = f"""{self.response["protocol"]} {self.response["status"]} {self.response["message"]}
                {headers}\n\n
                {self.response["body"]}\n
            """

            self.writer.write(response.encode("utf-8"))
            await self.writer.drain()
            self.writer.close()
            await self.writer.wait_closed()
        except Exception as e:
            print("Error while sending response : ", str(e))
        finally:
            await self.logger.AllLog(
                status     = status,
                protocol   = self.info["protocol"],
                src_ip     = self.info["src_ip"],
                dst_ip     = self.writer.transport.get_extra_info('peername')[0],
                method     = self.info["method"],
                path       = self.info["path"],
                start_time = self.info["start"],
            )

    async def send_file(self, path: str = "") -> None:
        """
        Send a file to the client.

        Args:
        path (str): The path to the file to send.
        """

        status = 200
        problem = "None"

        try :
            async with aio_open(path, "r", encoding="utf-8") as file:
                content = await file.read()
        except FileNotFoundError:
            status = 500
            content = "File not found"
            problem = "File not found"
        except Exception as e:
            status = 500
            content = str(e)
            problem = str(e)

        content_type = {
            "html": "text/html",
            "css": "text/css",
            "js": "application/javascript",
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "gif": "image/gif",
            "json": "application/json",
            "txt": "text/plain",
            "xml": "application/xml",
            "pdf": "application/pdf",
            "mp3": "audio/mpeg",
            "mp4": "video/mp4",
            "avi": "video/x-msvideo",
            "mov": "video/quicktime",
            "swf": "application/x-shockwave-flash",
            "zip": "application/zip",
            "exe": "application/x-msdownload",
            "tar": "application/x-tar",
            "gz": "application/x-gzip",
            "bz2": "application/x-bzip2",
            "rar": "application/x-rar",
            "7z": "application/x-7z-compressed",
            "iso": "application/x-iso9660-image",
            "doc": "application/msword",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "ppt": "application/vnd.ms-powerpoint",
            "md": "text/markdown",
        }.get(path.split(".")[-1], "text/plain")

        await self.send(content, status, content_type)

        await self.logger.AllLog(
            status     = status,
            protocol   = self.info["protocol"],
            src_ip     = self.info["src_ip"],
            dst_ip     = self.writer.transport.get_extra_info('peername')[0],
            method     = self.info["method"],
            path       = self.info["path"],
            start_time = self.info["start"],
            problem    = problem
        )

    async def send_json(self, data: dict | str = "", status: int = 200) -> None:
        """
        Send JSON data to the client.

        Args:
        data (dict | str): The JSON data to send (can be a path to a JSON file).
        status (int): The HTTP status code.
        """
        message = "None"

        if isinstance(data, str):
            try :
                async with aio_open(data, "r") as file:
                    data = await load(file.read())
            except FileNotFoundError:
                data = {"error": "File not found"}
                status = 500
                message = "File not found"
            except Exception as e:
                data = {"error": str(e)}
                status = 500
                message = str(e)

        self.response = {
            "protocol": "HTTP/1.1",
            "status": status,
            "message": self._get_status_message(status),
            "headers": {
                "Content-Type": "application/json; charset=utf-8",
                "Connection": "close",
            },
            "body": dumps(data),
        }

        await self._run_middlewares()

        headers = "\n".join([f"{key}: {value}" for key, value in self.response["headers"].items()])

        response = f"""{self.response["protocol"]} {self.response["status"]} {self.response["message"]}
{headers} \r\n
{self.response["body"]}\n
        """

        self.writer.write(response.encode("utf-8"))
        await self.writer.drain()
        self.writer.close()
        await self.writer.wait_closed()

        await self.logger.AllLog(
            status      = status,
            protocol    = self.info["protocol"],
            src_ip      = self.info["src_ip"],
            dst_ip      = self.writer.transport.get_extra_info("peername")[0],
            method      = self.info["method"],
            path        = self.info["path"],
            start_time  = self.info["start"],
            problem     = message
        )

    @staticmethod
    def _get_status_message(status: int = 0) -> str:
        """Helper method to get standard HTTP status messages."""
        return {
            200: "OK", 
            404: "Not Found", 
            500: "Internal Server Error"
        }.get(
            status, "Unknown Status"
        )

    async def _run_middlewares(self) -> None:
        """Run middlewares."""
        for middleware in self.middlewares:
            await middleware(self.request, self)


class Router:
    """
    Router class to handle HTTP requests. Written with asyncio. Needs async coroutines for it. Enjoy the pain of using it :)
    """

    def __init__(self):
        self.routes = {
            "GET": {
                #       "/": index
            },
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

    def __str__(self):
        return f"HTTP Server on {self.host}:{self.port}, logging to {self.logger.filename}, debug mode : {self.debug}"

    """
    Definition of all methods (get, post, etc.)
    """
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

    def add_route(self, method: str, path:str) -> callable:
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

    def serve_static(self, path: str, directory: str) -> None:
        """
        Serve static files from the given directory.

        Args:
        path (str): The URL path to handle.
        directory (str): The directory to serve static files from.
        """

        path = self._path_to_regex(path + "<name>")
        self.routes["GET"][path] = lambda req, res: res.send_file(directory + "/" + req.params["name"])

    def add_middleware(self, middleware: callable) -> None:
        """
        Add a middleware to the router. The middleware will be called with the request and response objects. Needs to be async.
        """
        self.middlewares.append(middleware)

    """
    Run the server
    """
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
            await self.logger.debug(f"Serving on {addr[0]}:{addr[1]}")

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

        request_data = await reader.read(1024)
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
        """Shut the server down"""

        if self.server is None:
            exit(0)

        self.server._serving = False
        self.server.close() 
        if self.debug:
            await self.logger.debug("Server stopped by user")

    """
    Helper methods
    """
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


class WebSocket:
    """
    Hand made websocket, that can be used by the router and the user. Needs to be async.
    """

    def __init__(self):
        self.logger = Logger()
        self.MAGIC_STRING = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

        self._on_message = None
        self._on_init = None
        self._on_close = None

        self.clients = []

    def __str__(self):
        return "WebSocket"


    async def _websocket_handshake(self, reader:StreamReader, writer:StreamWriter):
        request = await reader.read(1024)

        # Lire la requête HTTP et obtenir la clé WebSocket
        headers = request.decode().split("\r\n")
        websocket_key = ""
        for header in headers:
            if header.startswith("Sec-WebSocket-Key:"):
                websocket_key = header.split(": ")[1].strip()

        # Générer la clé acceptée
        accept_key = b64encode(
            sha1((websocket_key + self.MAGIC_STRING).encode()).digest()
        ).decode()

        if "Upgrade: websocket" not in headers or "Connection: Upgrade" not in headers:
            writer.write("HTTP/1.1 400 Bad Request\r\n\r\n".encode())
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return False


        # Construire la réponse du handshake
        response = (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {accept_key}\r\n\r\n"
        )

        # Envoyer la réponse
        writer.write(response.encode())
        await writer.drain()

        # Connexion WebSocket établie
        if self.debug:
            await self.logger.debug("WebSocket: handshake done for client from " + str(writer.get_extra_info("peername")))
        return True

    def _encode_frame(self, message:str) -> bytes:
        # Encapsuler un message texte (opcode 0x1)
        frame = bytearray()
        frame.append(0b10000001)  # FIN bit et opcode (0x1 pour texte)
        message_bytes = message.encode("utf-8")
        length = len(message_bytes)

        # Gérer la longueur du message
        if length < 126:
            frame.append(length)
        elif length <= 0xFFFF:
            frame.append(126)
            frame.extend(length.to_bytes(2, "big"))
        else:
            frame.append(127)
            frame.extend(length.to_bytes(8, "big"))

        frame.extend(message_bytes)
        return bytes(frame)

    async def _decode_frame(self, reader:StreamReader) -> str:
        # Lire les premiers octets de l'en-tête de la trame
        first_byte, second_byte = await reader.read(2)
        opcode = first_byte & 0b00001111
        fin = first_byte & 0b10000000

        masked = second_byte & 0b10000000
        if not masked:
            raise ValueError("Client frames must be masked.")

        if opcode == 0x8:
            await self._send_close_frame()
            raise ConnectionAbortedError("Client sent a close frame.")

        # Lire la longueur du payload
        length = second_byte & 0b01111111
        if length == 126:
            length = int.from_bytes(await reader.read(2), "big")
        elif length == 127:
            length = int.from_bytes(await reader.read(8), "big")

        # Lire le masque (toujours présent pour les messages du client)
        mask = await reader.read(4)

        # Lire les données et les démêler avec le masque
        data = bytearray(await reader.read(length))
        for i in range(length):
            data[i] ^= mask[i % 4]

        return data.decode("utf-8")

    def define(self, element: str) -> callable:
        """
        Decorator to add a route to the router.

        Args:
        element (str): The element to handle (message, init, close).
        """

        def wrapper(handler: callable):
            if element == "message":
                self._on_message = handler
            elif element == "init":
                self._on_init = handler
            elif element == "close":
                self._on_close = handler

            return handler
        return wrapper

    async def _send_close_frame(self):
        frame = bytearray([0b10001000, 0])  # FIN bit et opcode 0x8 pour fermeture
        self.writer.write(frame)
        await self.writer.drain()

    async def _handle_client(self, reader:StreamReader, writer:StreamWriter):
        # Étape de handshake WebSocket
        await self._websocket_handshake(reader, writer)

        self.clients.append(writer)
        self.writer = writer

        if self._on_init:
            await self._on_init(self)

        try:
            while True:
                try :
                    # Lire un message WebSocket
                    message = await wait_for(self._decode_frame(reader), timeout=60)
                    if self.debug:
                        await self.logger.debug(f"WebSocket: received {message}")

                    # Émettre un message WebSocket
                    if self._on_message:
                        self.writer = writer
                        await self._on_message(self, message)
                except TimeoutError:
                    await self.logger.warn("WebSocket: Client timeout")
                except ConnectionAbortedError:
                    await self.logger.warn("WebSocket: Connection aborted by client")
                    break
                except ConnectionResetError:
                    await self.logger.warn("WebSocket: Connection reset by client")
                    break

        except ValueError:
            await self.logger.error("WebSocket: Client must be masked")
        finally:
            if self._on_close:
                await self._on_close(self)

            self.clients.remove(writer)
            writer.close()
            self.writer = None
            await writer.wait_closed()

    async def _run(self):
        self.server = await start_server(self._handle_client, self.host, self.port)

        if self.debug:
            await self.logger.debug(f"WebSocket server started on {self.host}:{self.port}")

        async with self.server:
            await self.server.serve_forever()

    async def serve(self, port: int=8765, host: str="127.0.0.1", debug: bool=False) -> None:
        """
        Start the event loop to handle requests.
        """
        self.host  = host
        self.port  = port
        self.debug = debug

        try:
            await self._run()
        except KeyboardInterrupt:
            self.shutdown()
        except Exception as e:
            await self.logger.error(e)

    async def _shutdown(self):
        """Shut the server down"""

        if self.server is None:
            exit(0)

        self.server._serving = False
        self.server.close() 
        if self.debug:
            await self.logger.debug("WebSocket server stopped by user")

    """
    Method usable by the user
    """

    async def send_all(self, message: str) -> None:
        """
        Send a message to all clients
        """

        for client in self.clients:
            client.write(self._encode_frame(message))
            await client.drain()

    async def send(self, message: str) -> None:
        """
        Send a message to the client
        """
        self.writer.write(self._encode_frame(message))
        await self.writer.drain()


class Server:
    """
    Easier way to run HTTP and WebSocket servers
    """

    def __init__(self, *args) -> None:
        self.toRun = args

    def __str__(self):
        return f"Server running {self.toRun}"

    async def serve(self, *args, **kwargs):
        try :
            tasks = []
            if len(self.toRun) > 1:
                for i in self.toRun:
                    arg = args[self.toRun.index(i)]
                    tasks.append(i.serve(**arg))

                await gather(*tasks)
            else:
                await self.toRun[0].serve(**kwargs)
        except KeyboardInterrupt:
            exit(0)

    def run(self, *args, **kwargs):
        try:
            run_async(self.serve(*args, **kwargs))
        except KeyboardInterrupt:
            exit(0)


class Logger:
    """
    Hand made logger, that can be used by the router and the user. Log in both console and file.
    """

    def __init__(self, filename: str = "pyn.log") -> None:
        self.filename = filename

    def __str__(self):
        return f"Logger writing to {self.filename}"

    async def AllLog(self, status: int = 0, protocol: str = "HTTP/1.1", src_ip: str = "", dst_ip: str = "", method: str = "", path: str = "", start_time: datetime = datetime.now(), **kwargs, ) -> None:
        """
        Log all the data to the console and to the log file. Recommand to use "info", "warn", "error" and "debug" instead if possible. Used by the router.
        """

        end = datetime.now()
        duration = (end - start_time).microseconds
        await self.fileLog(status, protocol, src_ip, dst_ip, duration, **kwargs)
        await self.consoleLog(status, dst_ip, method, duration, path)

    async def fileLog(self, status: int = 0, protocol: str = "HTTP/1.1", src_ip: str = "", dst_ip: str = "", duration: int = 0, **kwargs, ) -> None:
        """
        Write the data to the log file. Used by the router. Hard to understand, but great for debugging.
        """

        try:
            date = datetime.now().strftime("%d/%m/%Y %H:%M:%S.%f")
            level = "INFO" if status < 400 else "WARNING" if status < 500 else "ERROR"
            msg = ""

            for key, value in kwargs.items():
                msg += f" │ {key.upper()}={value}".ljust(28)
            try :
                data = f"[PYN] {date} │ {level.ljust(7)} │ SRC_IP={src_ip.ljust(15)} -> DST_IP={dst_ip.ljust(15)} │ DURATION={(str(duration)+"ms").ljust(10)} │ PROTO={protocol.ljust(7)} │ STATUS={status}{msg}\n"
                async with aio_open(self.filename, "a", encoding="utf-8") as file:
                    await file.write(data)
            except SyntaxError :
                pass
        except Exception as e:
            print("Failed to write to file:", e)

    async def consoleLog(self, status: int = 0, ip: str = "", method: str = "", duration: int = 0, path: str = "") -> None:
        """
        Write the data to the console. Used by the router. Easier than "fileLog" to understand.
        """

        date = f"\033[1m{datetime.now().strftime("%d/%m/%Y %H:%M:%S.%f")}\033[0m"

        status = f"{self._get_ansi_status(status)} {str(status).rjust(5).ljust(7)} \033[0m"
        method = f"{self._get_ansi_method(method)}{method.ljust(7)}\033[0m"

        print(f'[PYN] {date} │{status}│ {ip.rjust(15)} │ {str(duration).rjust(10)}ms │ {method} │ "{path}"')

    def _get_ansi_status(self, status: int = 0) -> str:
        """Helper method to get the ANSI color code for a given status code"""
        if status >= 200 and status < 300:
            return "\033[42m" # green
        elif status >= 300 and status < 400:
            return "\033[45m" # pink
        elif status >= 400 and status < 500:
            return "\033[41m" # red
        else:
            return "\033[43m" # yellow

    def _get_ansi_method(self, method: str = "") -> str:
        """Helper method to get the ANSI color code for a given HTTP method"""
        methods_colors = {
            "GET": "\033[34m",
            "POST": "\033[32m",
            "PUT": "\033[33m",
            "DELETE": "\033[31m",
            "PATCH": "\033[36m",
            "OPTIONS": "\033[35m",
        }

        return methods_colors.get(method, "\033[0m")

    async def write(self, message: str = "", level: str = "") -> None:
        """
        Method behind "info", "warning", "error" and "debug". Used by the router. Recommend to use "info", "warn", "error" and "debug" instead if possible.
        """
        try :
            date = f"\033[1m{datetime.now().strftime("%d/%m/%Y %H:%M:%S.%f")}\033[0m"
            status = f"\033[4{'1' if level == 'error' else '3' if level == 'warning' else '4' if level == 'debug' else '2'}m {level.upper().ljust(7)} \033[0m"

            print(f"[PYN] {date} │{status}│ {message}")

            try:
                async with aio_open(self.filename, "a", encoding="utf-8") as file :
                    message = f"[PYN] {date} │{status}│ {message}\n"
                    regex = compile(r"\033\[[0-9;]*[mK]")

                    message = sub(regex, '', message)

                    await file.write(message)
            except Exception as e:
                print(f"Error while writing in the file : {e}")
        except SyntaxError :
            pass

    async def info(self, message: str = "") -> None:
        """
        Log an information message. Used by the router. Recommended to use.
        """
        await self.write(message, "info")

    async def warn(self, message: str = "") -> None:
        """
        Log a warning message. Used by the router. Recommended to use.
        """
        await self.write(message, "warning")

    async def error(self, message: str = "") -> None:
        """
        Log an error message. Used by the router. Recommended to use.
        """
        await self.write(message, "error")

    async def debug(self, message: str = "") -> None:
        """
        Log a debug message. Used by the
        """
        await self.write(message, "debug")