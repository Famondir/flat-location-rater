import asyncio
from pprint import pprint
import time
from aiohttp import ClientSession, ClientConnectorError, ClientTimeout
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

class AsyncRequest:
    def __init__(self, urls: list):
        self.urls = urls
        self.queue = asyncio.Queue()
        self.results = []
        self.timeout = ClientTimeout(total=10)
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def send_request(self, url):
        try:
            async with ClientSession(timeout=self.timeout) as session:
                async with session.get(url) as response:
                    result = {"response": await response.text(), "url": url}
                    await self.queue.put(result)
        except ClientConnectorError as e:
            # logging.error(f"Connection error for {url}: {str(e)}")
            result = {"response": None, "url": url, "error": str(e)}
            await self.queue.put(result)
        except asyncio.TimeoutError as e:
            # logging.error(f"Timeout for {url}: {str(e)}")
            result = {"response": None, "url": url, "error": "timeout"}
            await self.queue.put(result)

    async def send_requests(self): 
        async with asyncio.TaskGroup() as group:
            for url in self.urls:
                group.create_task(self.send_request(url))

        while not self.queue.empty():
            self.results.append(await self.queue.get())
        
    def get_requests(self):
        asyncio.run(self.send_requests())

if __name__ == "__main__":
    start = time.time()
    async_request = AsyncRequest(["https://v6.bvg.transport.rest/journeys?from.latitude=52.543333&from.longitude=13.351686&from.address=ATZE+Musiktheater&to=900014101&departure=tomorrow+2pm&results=1"])
    async_request.get_requests()
    end = time.time()
    print(end - start)
    pprint(async_request.results)