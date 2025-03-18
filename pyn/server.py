"""
File where is defined the Server class
"""

from asyncio import gather, run as run_async


class Server:
    """
    Easier way to run HTTP and WebSocket servers
    """

    def __init__(self, *args) -> None:
        self.to_run = args

    def __str__(self):
        return f"Server running {self.to_run}"

    async def serve(self, *args, **kwargs):
        """Method to serve everything who was gave in arguments with the specified parameter"""
        try :
            tasks = []
            if len(self.to_run) > 1:
                for i in self.to_run:
                    arg = args[self.to_run.index(i)]
                    tasks.append(i.serve(**arg))

                await gather(*tasks)
            else:
                await self.to_run[0].serve(**kwargs)
        except KeyboardInterrupt:
            exit(0)

    def run(self, *args, **kwargs):
        """Darkside of the start"""
        try:
            run_async(self.serve(*args, **kwargs))
        except KeyboardInterrupt:
            exit(0)
