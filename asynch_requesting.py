import asyncio
from pprint import pprint
from aiohttp import ClientSession
import time

class AsyncRequest:
    def __init__(self, urls: list):
        self.urls = urls
        self.queue = asyncio.Queue()
        self.results = []
        
    async def send_request(self, url):
        async with ClientSession() as session:
            async with session.get(url) as response:
                result = {"response": await response.text(), "url": url}
                await self.queue.put(result)

    async def get_requests(self):       
        async with asyncio.TaskGroup() as group:
            for url in self.urls:
                group.create_task(self.send_request(url))

        while not self.queue.empty():
            self.results.append(await self.queue.get())

if __name__ == "__main__":
    start = time.time()
    async_request = AsyncRequest(["https://v6.bvg.transport.rest/journeys?from.latitude=52.543333&from.longitude=13.351686&from.address=ATZE+Musiktheater&to=900014101&departure=tomorrow+2pm&results=1"])
    asyncio.run(async_request.get_requests())
    end = time.time()
    print(end - start)
    pprint(async_request.results)