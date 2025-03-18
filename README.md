# PYN

A simple yet powerful handmade python router framework.
It's made around the `asyncio` library and supports both HTTP and WebSocket.
It isn't recommended to use it in production, it's more a project for learning and experimentation.
You're free to use it, sell it, share it, modify it, whatever you want.

----------------------------------------------

## Requirements

- `aiofiles`    24.1.0
- `python`      >= 3.8

----------------------------------------------

## Installation

Just download `pyn.py` and import it in your project. It will be ready to use.
The file is only 890 lines long and it's only 30.02 KB.

----------------------------------------------

## Usage

Pyn support both HTTP and WebSocket.

----------------------------------------------

### [HTTP](doc/http.md)

```python
import pyn

router = pyn.Router()

async def hello(req: pyn.Request, res: pyn.Response) -> None:
    await res.send_json({"hello": "world"})

router.get("/hello", hello)

server = pyn.Server(router)
server.run(
    host="127.0.0.1",
    port=8000
)
```

You can also use the `@router.add_route` decorator to add routes.

```python
@router.add_route("GET", "/hello")
async def hello(req: pyn.Request, res: pyn.Response) -> None:
    await res.send_json({"hello": "world"})
```

The `Request` and `Response` classes are simple wrappers around the `aiohttp` classes.

Supported HTTP methods:

- `GET`
- `POST`
- `PUT`
- `DELETE`
- `PATCH`
- `HEAD`
- `OPTIONS`

----------------------------------------------

#### Middlewares

The `router.add_middleware` function can be used to add middleware to the router. The middleware will be called with the request and response objects just before sending the response. Needs to be async.

```python
import pyn

router = pyn.Router()

@router.add_route("GET", "/")
async def index(req: pyn.Request, res: pyn.Response) -> None:
    await res.send_file("index.html")

async def middleware(req: pyn.Request, res: pyn.Response) -> None:
    if req.headers.get("Authorization") == "123456":
        await res.send_json({"hello": "world"})
    else:
        pass

router.add_middleware(middleware)

server = pyn.Server(router)
server.run(
    host="127.0.0.1",
    port=8000
)
```

----------------------------------------------

#### Static files

```python
import pyn

router = pyn.Router()

router.serve_static("/static/", "./public") # Serve files from the `./public` directory 

server = pyn.Server(router)
server.run(
    host="127.0.0.1",
    port=8000,
)
```

----------------------------------------------

### [WebSocket](doc/websocket.md)

```python
import pyn

ws = pyn.WebSocket()
messages = []

@ws.define("init")
async def on_init(ws: pyn.WebSocket) -> None:
    for message in messages:
        await ws.send_all(message)

@ws.define("message")
async def on_message(ws: pyn.WebSocket, message: str) -> None:
    await ws.send(message)

@ws.define("close")
async def on_close(ws: pyn.WebSocket) -> None:
    print("Connection closed")

server = pyn.Server(ws)
server.run(
    host="127.0.0.1",
    port=8000
)
```

----------------------------------------------

### Running both HTTP and WebSocket

```python
import pyn

ws = pyn.WebSocket()
router = pyn.Router()
messages = []

@ws.define("init")
async def on_init(ws: pyn.WebSocket) -> None:
    for message in messages:
        await ws.send(message)

@ws.define("message")
async def on_message(ws: pyn.WebSocket, message: str) -> None:
    await ws.send(message)

@router.add_route("GET", "/")
async def index(req: pyn.Request, res: pyn.Response) -> None:
    await res.send_file("index.html")

server = pyn.Server(router, ws)
server.run(
    {"host": "127.0.0.1", "port": 8000, "debug": True},
    {"host": "127.0.0.1", "port": 8001, "debug": False}
)
```

The `debug` option will just activate or deactivate some log messages. It's recommended to set it to `True` in production and development (yeah it should be always `True`).

----------------------------------------------

### [Logger](doc/logger.md)

```python
import pyn

logger = pyn.Logger()
logger.info("Hello, world!")
```

It will log the message to the console and in the `pyn.log` file.

----------------------------------------------

## Known issues

- Nothing is tested, so things may not work or be buggy.
- Say to many things in console when you kill the server with Ctrl+C
    > Reason : Need to destroy all tasks before killing the server
- Crash every sockets when sometimes one disconnect, causing him to lost every connection forever (yeah big bug)

----------------------------------------------

## Contributing

The project is open source. You can fork it and make your own version.
Contributions are not yet open, but may be in the futur

----------------------------------------------

## Future plans

- Add `pyn` as a package
- Add a template engine for `pyn`
- Add more documentation
- Add tests

----------------------------------------------

## License

Pyn is under the [MIT License](LICENSE), so you're free to use it in any way you want.
