"""
File to define Response class.
"""

from asyncio  import StreamWriter
from json     import load, dumps
from aiofiles import open as aio_open
from .request import Request
from .logger  import Logger


class Response:
    """
    Response class used to send HTTP responses to the client. 
    Written with asyncio. 
    You can use real asyncio with "response.writer" if needed (asyncio.StreamWriter).
    """

    def __init__(
        self, writer: StreamWriter = None,
        info: dict = None,
        middlewares: list[callable] = None,
        request: Request = None
    ):
        self.writer = writer
        self.logger = Logger()
        self.info = {} if info is None else info
        self.middlewares = [] if middlewares is None else middlewares
        self.request = request
        self.response = {}

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

            response = f"{self.response['protocol']} {self.response['status']} {self.response['message']}\n{headers}\n\n\n{self.response['body']}\n"

            self.writer.write(response.encode("utf-8"))
            await self.writer.drain()
            self.writer.close()
            await self.writer.wait_closed()
        except Exception as e:
            print("Error while sending response : ", str(e))
        finally:
            await self.logger.all_log(
                status     = status,
                protocol   = self.info["protocol"],
                src_ip     = self.info["src_ip"],
                dst_ip     = self.writer.transport.get_extra_info('peername')[0],
                method     = self.info["method"],
                path       = self.info["path"],
                start_time = self.info["start"],
            )

    async def template(
        self,
        status: int = 200,
        head: str = "",
        body: str = ""
    ):
        """
        Helper method we set directly the HTML code in place.
        """
        html = f"<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'>{head}</head><body>{body}</body></html>"
        await self.send(html, status)

    async def file(self, path: str = "") -> None:
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

        await self.logger.all_log(
            status     = status,
            protocol   = self.info["protocol"],
            src_ip     = self.info["src_ip"],
            dst_ip     = self.writer.transport.get_extra_info('peername')[0],
            method     = self.info["method"],
            path       = self.info["path"],
            start_time = self.info["start"],
            problem    = problem
        )

    async def json(self, data: dict | str = "", status: int = 200) -> None:
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

        response = f"""{self.response["protocol"]} {self.response["status"]} {self.response["message"]}\n{headers} \r\n\n{self.response["body"]}\n"""

        self.writer.write(response.encode("utf-8"))
        await self.writer.drain()
        self.writer.close()
        await self.writer.wait_closed()

        await self.logger.all_log(
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
        # Helper method to get standard HTTP status messages.
        return {
            200: "OK",
            404: "Not Found",
            500: "Internal Server Error"
        }.get(
            status, "Unknown Status"
        )

    async def _run_middlewares(self) -> None:
        # Run middlewares.
        for middleware in self.middlewares:
            await middleware(self.request, self)
