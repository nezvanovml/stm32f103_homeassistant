# version 0.1 (20240310)
import logging
import aiohttp
import socket

_LOGGER = logging.getLogger(__name__)

class STMDevice():

    def __init__(self, ip_address: str):
        self._ip_address = ip_address
        try:
            socket.inet_aton(self._ip_address)
            pass
        except socket.error:
            raise InvalidIP


    async def api_request(self, endpoint: str, method: str, params: dict | None = None):
        if method not in ["GET", "POST"]:
            raise InvalidMethod

        if not params:
            params = "{}"

        _LOGGER.info(f"Request: {endpoint} ({method}): {params}")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.request(method, f"http://{self._ip_address}/{endpoint}",
                                           params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        _LOGGER.error(
                            f"APIError. IP address: {self._ip_address}. Endpoint: {endpoint}. Params: {params}. Status: {response.status} ")
                        raise APIError
            except Exception as error:
                _LOGGER.error(f"Error connecting to API. Error: {error}. IP address: {self._ip_address}. Endpoint: {endpoint}. Params: {params}. ")
                raise ConnectionError

    @property
    async def system_info(self):
        '''Получение системной информации от устройства'''
        data = await self.api_request("system_info", "GET")
        return data

    @property
    async def state(self):
        '''Получение самого последнего статуса'''
        data = await self.api_request("state", "GET")
        return data

    @property
    async def version(self):
        '''Получение версии'''
        data = await self.system_info
        return data.get("version", 0)

    @property
    async def ip_address(self):
        '''Получение ip'''
        return self._ip_address


class InvalidIP(Exception):
    """Error to indicate there is an invalid IP."""

class InvalidMethod(Exception):
    """Error to indicate there is an invalid method."""

class APIError(Exception):
    """Error to indicate there is an error in API response."""

class ConnectionError(Exception):
    """Error to indicate there is an error in connection."""