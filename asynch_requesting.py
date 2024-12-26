import asyncio
from aiohttp import ClientSession
import json
import time

async def hello(url: str, queue: asyncio.Queue):
    async with ClientSession() as session:
        async with session.get(url) as response:
            result = {"response": await response.text(), "url": url}
            await queue.put(result)


async def main():
    # I'm using test server localhost, but you can use any url
    url = "https://v6.bvg.transport.rest/journeys?from.latitude=52.543333&from.longitude=13.351686&from.address=12623+Berlin&to=900014101&departure=tomorrow+2pm&results=1"
    results = []
    queue = asyncio.Queue()
    async with asyncio.TaskGroup() as group:
        for i in range(130):
            group.create_task(hello(url, queue))

    while not queue.empty():
        results.append(await queue.get())
    
    # print(json.dumps(results))

if __name__ == "__main__":
    start = time.time()
    asyncio.run(main())
    end = time.time()
    print(end - start)