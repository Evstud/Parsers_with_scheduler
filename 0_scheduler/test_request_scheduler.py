import aiohttp
import asyncio
import json


SCHEDULER_ADD_URL = 'http://127.0.0.1:9001/scheduler/add/'
SCHEDULER_TURN_URL = 'http://127.0.0.1:9001/scheduler/action/'


async def send_add_request(name):
    async with aiohttp.ClientSession() as session:
        async with session.post(url=SCHEDULER_ADD_URL, json={'scrapper_name': name}) as response:
            print(await response.text())


async def send_turn_on_request(name):
    async with aiohttp.ClientSession() as session:
        async with session.post(
                url=SCHEDULER_TURN_URL,
                json={'scrapper_name': name, 'action': 'turn_on'}) as response:
            print(await response.text())


async def send_turn_off_request(name):
    async with aiohttp.ClientSession() as session:
        async with session.post(
                url=SCHEDULER_TURN_URL,
                json={'scrapper_name': name, 'action': 'turn_off'}) as response:
            print(await response.text())


if __name__ == "__main__":
    asyncio.run(send_add_request(name='first_scrapper'))
    # asyncio.run(send_turn_on_request(name='first_scrapper'))
    # asyncio.run(send_turn_off_request(name='first_scrapper'))