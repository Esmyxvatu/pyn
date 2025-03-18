# [PYN](../README.md)

----------

## Websocket

Websockets classes are made on a special way.
First, declare a variable associated to a websocket object.

```python
import pyn

messages = []

ws = pyn.WebSocket()
```

Then, define the events you want to listen to.

Events supported :

- `init` when a new connection is opened
- `message` when a message is received
- `close` when the connection is closed

You define them with the `@ws.define` decorator on an async function.

```python
@ws.define("init")
async def on_init(ws: pyn.WebSocket) -> None:
    for message in messages:
        await ws.send(message)

@ws.define("message")
async def on_message(ws: pyn.WebSocket, message: str) -> None:
    messages.append(message)
    await ws.send_all(message)

@ws.define("close")
async def on_close(ws: pyn.WebSocket) -> None:
    print("Connection closed")
```

You can send messages to the last connected client with the `ws.send` method (it will be changed when you receive a message).

```python
ws.send(message)
```

Or send messages to all connected clients with the `ws.send_all` method.

```python
ws.send_all(message)
```

Finally, start the server with the `ws.serve` method or with a `Server` object.

```python
ws.serve(port=3001, host="127.0.0.1", debug=True)

# or

server = pyn.Server(ws)
server.run(port=3001, host="127.0.0.1", debug=True)

```

It's conseilled to use a `Server` object in production. For two main reasons:

- If you add a router, it will be easier to launch both
- It's like that i tested so....

----------

## All the code

Here is all the code for this example.

```python
import pyn

messages = []
ws = pyn.WebSocket()

@ws.define("init")
async def on_init(ws: pyn.WebSocket) -> None:
    for message in messages:
        await ws.send(message)

@ws.define("message")
async def on_message(ws: pyn.WebSocket, message: str) -> None:
    messages.append(message)
    await ws.send_all(message)

@ws.define("close")
async def on_close(ws: pyn.WebSocket) -> None:
    print("Connection closed")

server = pyn.Server(ws)
server.run(
    host="127.0.0.1",
    port=8000
    # By default, debug is false, it's more readable, but it can miss some messages
)
```

## Issues

- Nothing is tested, so things may not work or be buggy.
- Say to many things in console when you kill the server with Ctrl+C
    > Reason : Need to destroy all tasks before killing the server
- Many log messages not necessary when on debug
    > Reason : I added to much log messages

## Future plans

- Add a `ws.send_except` method
- Add a system of rooms
