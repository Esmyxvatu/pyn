"""
File defining the Request Class.
"""

class Request:
    """
    Request class used to handle HTTP requests. 
    Written with asyncio. 
    You can use real asyncio with "request.reader" if needed (asyncio.StreamReader).
    """


    def __init__(
        self, method: str,
        path: str,
        headers: dict = None,
        body: str = "",
        params: dict = None
    ):
        self.method = method
        self.path = path
        self.headers = {} if headers is None else headers
        self.body = body
        self.params = {} if params is None else params

    def __str__(self):
        return f"Method : {self.method}\nPath : {self.path}\nHeaders : {self.headers}\nBody : {self.body}\nParams : {self.params}"
