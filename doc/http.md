# [PYN](../README.md)

----------

## HTTP

The http router is made around the `asyncio` library. You can access the real asyncio `response.writer` if needed.
It supports `GET`, `POST`, `PUT`, `DELETE`, `PATCH` and `OPTIONS` requests by default, but you can "create" your own by using the decorator.


---------------------------

### Adding a route

You can choose between the decorator `@router.add_route` or the function `router.[method]` to add a path.

```python
import pyn

router = pyn.Router()

@router.add_route("GET", "/")
async def index(req: pyn.Request, res: pyn.Response) -> None:
    await res.send_file("index.html")
```

```python
import pyn

router = pyn.Router()

async def index(req: pyn.Request, res: pyn.Response) -> None:
    await res.send_file("index.html")

router.get("/", index)
```

-------------

### Middleware

You can add middleware to the router. The middleware will be called with the request and response objects just before sending the response. Needs to be async.

```python
import pyn

router = pyn.Router()

@router.add_route("GET", "/")
async def index(req: pyn.Request, res: pyn.Response) -> None:
    await res.send_file("index.html")

async def middleware(req: pyn.Request, res: pyn.Response) -> None:
    if req.headers.get("Authorization") == "123456":
        await res.response["body"] = "You are logged in!"
    else:
        pass

router.add_middleware(middleware)
```

-------------

### Static files

You can serve static files from the given directory.

```python
import pyn

router = pyn.Router()

@router.add_route("GET", "/")
async def index(req: pyn.Request, res: pyn.Response) -> None:
    await res.send_file("index.html")
```

-----------

### Send functions

You can use three functions to send data to the client:
  1. `res.send()`, who takes three arguments :
    - content (str): The content to send in the HTTP body.
    - status (int): The HTTP status code. Defaults to 200.
    - content_type (str): The content type of the response. Defaults to "text/html".

  2. `res.send_file()`, who takes one argument :
    - path (str): The path of the file to send.

  3. `res.send_json()`, who takes two argument :
    - data (dict or str): The data to send in the HTTP body. If it's a str, it's treated as a path to a JSON file.
    - status (int): The HTTP status code. Defaults to 200.

```python
import pyn

router = pyn.Router()

@router.add_route("GET", "/")
async def index(req: pyn.Request, res: pyn.Response) -> None:
    await res.send_file("index.html")
    await res.send_json({"hello": "world"}, status=201)
    await res.send("Hello World!", status=201)
```

-------------------------------

### Run the server

To run the router, you can or use a `Server` object or the `serve` function.

```python
import pyn

router = pyn.Router()

@router.add_route("GET", "/")
async def index(req: pyn.Request, res: pyn.Response) -> None:
    await res.send_file("index.html")

server = pyn.Server(router)
server.run(
    host="127.0.0.1",
    port=8000
)
```

```python
import pyn

router = pyn.Router()

async def index(req: pyn.Request, res: pyn.Response) -> None:
    await res.send_file("index.html")

router.get("/", index)

router.serve(
    host="127.0.0.1",
    port=8000
)
```