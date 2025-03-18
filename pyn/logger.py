"""
File to define the Logger class.
"""

from datetime import datetime
from re       import sub
from aiofiles import open as aio_open


class Logger:
    """
    Hand made logger, that can be used by the router and the user. 
    Log in both console and file.
    The output file is defined by the user.
    Default file: pyn.log.
    """

    def __init__(self, filename: str = "pyn.log") -> None:
        self.filename = filename

    def __str__(self):
        return f"Logger writing to {self.filename}"

    async def all_log(
        self,
        status: int = 0,
        protocol: str = "HTTP/1.1",
        src_ip: str = "",
        dst_ip: str = "",
        method: str = "",
        path: str = "",
        start_time: datetime = datetime.now(),
        **kwargs,
    ) -> None:
        """
        Log all the data to the console and to the log file. 
        Recommand to use "info", "warn", "error" or "debug" instead if possible. 
        Used by the router.
        """

        end = datetime.now()
        duration = (end - start_time).microseconds

        kwargs["path"] = f'"{path}"'

        await self.file_log(status, protocol, src_ip, dst_ip, duration, **kwargs)
        await self.console_log(status, dst_ip, method, duration, path)

    async def file_log(
        self,
        status: int = 0,
        protocol: str = "HTTP/1.1",
        src_ip: str = "",
        dst_ip: str = "",
        duration: int = 0,
        **kwargs,
    ) -> None:
        """
        Write the data to the log file. 
        Used by the router. 

        TODO Make it easier to understand
        """

        try:
            date = datetime.now().strftime("%d/%m/%Y %H:%M:%S.%f")
            level = "INFO" if status < 400 else "WARNING" if status < 500 else "ERROR"
            msg = ""

            for key, value in kwargs.items():
                msg += f" │ {key.upper()}={value}".ljust(28) if value is None else ""
            try :
                data = f"[PYN] {date} │ {level.ljust(7)} │ SRC_IP={src_ip.ljust(15)} -> DST_IP={dst_ip.ljust(15)} │ DURATION={(str(duration)+'ms').ljust(10)} │ PROTO={protocol.ljust(7)} │ STATUS={status}{msg}\n"
                async with aio_open(self.filename, "a", encoding="utf-8") as file:
                    await file.write(data)
            except SyntaxError :
                pass
        except Exception as e:
            print("Failed to write to file:", e)

    async def console_log(
        self,
        status: int = 0,
        ip: str = "",
        method: str = "",
        duration: int = 0,
        path: str = ""
    ) -> None:
        """
        Write the data to the console. 
        Used by the router. 
        Easier than "file_log" to understand.
        """

        date = f" \033[1m{datetime.now().strftime('%d/%m/%Y %H:%M:%S.%f')}\033[0m "

        status = f"{self._get_ansi_status(status)} {str(status).rjust(5).ljust(7)} \033[0m"
        method = f" {self._get_ansi_method(method)}{method.ljust(7)}\033[0m "

        print(
            f'[PYN]{date}│{status}│ {ip.rjust(15)} │ {str(duration).rjust(10)}ms │{method}│ "{path}"'
        )

    def _get_ansi_status(self, status: int = 0) -> str:
        # Helper method to get the ANSI color code for a given status code
        if 200 <= status < 300:
            return "\033[42m" # green
        if 300 <= status < 400:
            return "\033[45m" # pink
        if 400 <= status < 500:
            return "\033[41m" # red

        return "\033[43m" # yellow

    def _get_ansi_method(self, method: str = "") -> str:
        # Helper method to get the ANSI color code for a given HTTP method
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
        Method behind "info", "warning", "error" and "debug". 
        Used by the router. 
        Recommend to use "info", "warn", "error" or "debug" instead if possible.
        """
        try :
            date = f"\033[1m{datetime.now().strftime('%d/%m/%Y %H:%M:%S.%f')}\033[0m"
            status = f"""\033[4{
                '1' if level == 'error'
                else '3' if level == 'warning'
                else '4' if level == 'debug'
                else '2'}m {level.upper().ljust(7)} \033[0m"""

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
