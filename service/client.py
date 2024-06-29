import asyncio
from asyncio import Semaphore
from typing import Any

import httpx

from settings import settings


class Client:
    """
    This is the client to sending keypress to IP-phones
    """

    HEADERS = {"Content-Type": "text/xml;charset=utf-8"}  # application/xml
    AUTH = httpx.BasicAuth(settings.USER, settings.USER_PWD)
    PAUSE: int = settings.PAUSE

    @property
    def client(self):
        return httpx.AsyncClient(timeout=3.0)

    async def send_keypress(
        self, ip: str, key_navigation: list[str], semaphore: Semaphore
    ) -> dict[str, Any]:
        """
        Send keypress to IP-phone
        :param ip: phone ip address for connection
        :param key_navigation: key navigation list sending to phone
        :param semaphore: number of concurrent connections
        :return: dict with ip address and response code
        """
        async with semaphore:
            url = f"http://{ip}/CGI/Execute"
            responses = []
            async with self.client as client:
                for xml in key_navigation:
                    resp = await client.post(
                        url,
                        auth=self.AUTH,
                        headers=self.HEADERS,
                        data={"XML": xml},
                    )
                    responses.append(resp.status_code)
                    await asyncio.sleep(self.PAUSE)
            return {
                "ip": ip,
                "response": 200 if all(i <= 400 for i in responses) else responses[-1],
            }
