"""
File where the WebSocket is defined.
"""

from asyncio  import StreamReader, StreamWriter, start_server, wait_for
from hashlib  import sha1
from base64   import b64encode
from .logger  import Logger


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

        self.writer = None
        self.host = None
        self.port = None
        self.server = None
        self.debug = False

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
            await self.logger.debug(
                "WebSocket: handshake done for client from " + 
                str(writer.get_extra_info("peername"))
            )
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
            self._shutdown()
        except Exception as e:
            await self.logger.error(e)

    async def _shutdown(self):
        # Shut the server down

        if self.server is None:
            exit(0)

        self.server._serving = False
        self.server.close()
        if self.debug:
            await self.logger.debug("WebSocket server stopped by user")

    # Client Method

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
